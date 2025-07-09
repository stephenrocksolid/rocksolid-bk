from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from typing import Optional, List, Any
from django.db.models import Sum
from django.utils import timezone


class Customer(models.Model):
    """Customer model for storing client information"""
    
    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
        ('due_on_receipt', 'Due on Receipt'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Company name")
    contact_person = models.CharField(max_length=200, blank=True, null=True, help_text="Primary contact person")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='United States')
    
    # Business Information
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="Tax ID or Business Number")
    payment_terms = models.CharField(
        max_length=20, 
        choices=PAYMENT_TERMS_CHOICES
    )
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # type: ignore
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self) -> str:
        return str(self.name)
    
    @property
    def full_address(self) -> str:
        """Return formatted full address"""
        parts = [self.address, self.city, self.state, self.zip_code, self.country]
        return ', '.join(filter(None, parts))
    
    @property
    def current_balance(self) -> Decimal:
        """Calculate current account balance"""
        # Simple calculation: Total Invoiced - Total Payments
        total_invoiced = self.invoices.exclude(status='cancelled').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        total_payments = self.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return total_invoiced - total_payments


class InvoiceNumberTracker(models.Model):
    """Singleton model to track the next invoice number"""
    next_number = models.PositiveIntegerField(default=1)  # type: ignore

    def __str__(self) -> str:
        return f"Next Invoice Number: {self.next_number}"

    @classmethod
    def get_solo(cls) -> 'InvoiceNumberTracker':
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class Invoice(models.Model):
    """Invoice model for storing invoice headers"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, help_text="Unique invoice number")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice Details
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Financial Information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    finance_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    enable_finance_charge = models.BooleanField(default=True, help_text="Enable automatic finance charge calculation")
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-issue_date', '-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} - {self.customer.name}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to auto-generate invoice number and calculate totals"""
        skip_calculation = kwargs.pop('skip_calculation', False)
        
        if not self.invoice_number:
            tracker = InvoiceNumberTracker.get_solo()
            self.invoice_number = str(tracker.next_number)
            tracker.next_number = tracker.next_number + 1  # type: ignore
            tracker.save()
        else:
            # If manually set and higher than tracker, update tracker
            try:
                num = int(str(self.invoice_number))
                if num > 0:
                    tracker = InvoiceNumberTracker.get_solo()
                    if num >= tracker.next_number:
                        tracker.next_number = num + 1  # type: ignore
                        tracker.save()
            except (ValueError, TypeError):
                pass  # Allow non-integer invoice numbers, but don't update tracker
        
        # Calculate totals unless skipped
        if not skip_calculation:
            self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self) -> None:
        """Calculate invoice totals"""
        # Calculate subtotal from line items
        self.subtotal = sum(item.total for item in self.items.all())
        
        # Calculate tax
        self.tax_amount = (self.subtotal - self.discount_amount) * self.tax_rate
        
        # Calculate finance charge based on payment terms
        self.calculate_finance_charge()
        
        # Calculate total (including finance charge)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount + self.finance_charge
    
    def calculate_finance_charge(self) -> None:
        """Calculate monthly compounding finance charge (1.5% per month)"""
        # Only calculate finance charge if enabled
        if not self.enable_finance_charge:
            self.finance_charge = Decimal('0.00')
            return
        
        # Calculate months past due (rounded up to nearest month)
        today = timezone.now().date()
        days_past_due = (today - self.due_date).days
        
        # Only apply finance charge if past due
        if days_past_due > 0:
            # Calculate months past due (round up to nearest month)
            months_past_due = (days_past_due + 29) // 30  # Round up to nearest month
            
            # Calculate the base balance (subtotal + tax - discount - payments)
            base_balance = self.subtotal + self.tax_amount - self.discount_amount - self.paid_amount
            
            if base_balance > 0:
                # Calculate monthly compounding finance charge
                # Formula: base_balance * (1.015)^months - base_balance
                monthly_rate = Decimal('1.015')  # 1.5% = 1.015
                compounded_amount = base_balance * (monthly_rate ** months_past_due)
                self.finance_charge = compounded_amount - base_balance
            else:
                self.finance_charge = Decimal('0.00')
        else:
            self.finance_charge = Decimal('0.00')
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return self.status == 'open' and self.due_date < timezone.now().date()
    
    @property
    def paid_amount(self) -> Decimal:
        """Calculate total amount paid"""
        return self.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance, accounting for customer account balance"""
        # Basic invoice balance
        invoice_balance = self.total_amount - self.paid_amount
        
        # Get customer's account balance (negative means they have credit)
        customer_balance = self.customer.current_balance
        
        # If customer has credit (negative balance), apply it to this invoice
        if customer_balance < 0:
            # Apply the credit to reduce the invoice balance
            # The credit amount is the absolute value of the negative balance
            credit_amount = abs(customer_balance)
            adjusted_balance = invoice_balance - credit_amount
            # Balance due cannot be negative
            return max(adjusted_balance, Decimal('0.00'))  # type: ignore
        
        # If customer has no credit, return the normal invoice balance
        return invoice_balance
    
    @property
    def account_balance_including_current(self) -> Decimal:
        """Calculate account balance including the current invoice"""
        # Calculate total invoiced excluding this invoice
        other_invoices_total = self.customer.invoices.exclude(
            status='cancelled'
        ).exclude(
            id=self.id
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Get total payments
        total_payments = self.customer.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Calculate: (other invoices + current invoice) - payments
        return other_invoices_total + self.total_amount - total_payments


class InvoiceItem(models.Model):
    """Invoice line items"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
    
    def __str__(self) -> str:
        return f"{self.description} - {self.invoice.invoice_number}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to calculate total"""
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment model for tracking customer payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Check number, transaction ID, etc.")
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self) -> str:
        return f"Payment {self.reference_number or self.id} - {self.customer.name} - ${self.amount}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to update invoice status if needed"""
        super().save(*args, **kwargs)
        
        # Update invoice status if this payment covers the full amount
        if self.invoice:
            if self.invoice.balance_due <= 0:
                self.invoice.status = 'paid'
                self.invoice.save()

# Signal handlers to keep invoice totals up-to-date
def update_invoice_totals(invoice: Invoice) -> None:
    invoice.calculate_totals()
    invoice.save(update_fields=[
        'subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'updated_at'
    ])

@receiver(post_save, sender=InvoiceItem)
def update_invoice_on_item_save(sender: Any, instance: InvoiceItem, **kwargs: Any) -> None:
    update_invoice_totals(instance.invoice)

@receiver(post_delete, sender=InvoiceItem)
def update_invoice_on_item_delete(sender: Any, instance: InvoiceItem, **kwargs: Any) -> None:
    update_invoice_totals(instance.invoice)
