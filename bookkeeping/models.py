from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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
        choices=PAYMENT_TERMS_CHOICES, 
        default='net_30'
    )
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [self.address, self.city, self.state, self.zip_code, self.country]
        return ', '.join(filter(None, parts))
    
    @property
    def current_balance(self):
        """Calculate current account balance"""
        # Simple calculation: Total Invoiced - Total Payments
        total_invoiced = self.invoices.exclude(status='cancelled').aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        total_payments = self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return total_invoiced - total_payments


class InvoiceNumberTracker(models.Model):
    """Singleton model to track the next invoice number"""
    next_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Next Invoice Number: {self.next_number}"

    @classmethod
    def get_solo(cls):
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
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate invoice number and calculate totals"""
        skip_calculation = kwargs.pop('skip_calculation', False)
        
        if not self.invoice_number:
            tracker = InvoiceNumberTracker.get_solo()
            self.invoice_number = str(tracker.next_number)
            tracker.next_number += 1
            tracker.save()
        else:
            # If manually set and higher than tracker, update tracker
            try:
                num = int(str(self.invoice_number))
                if num > 0:
                    tracker = InvoiceNumberTracker.get_solo()
                    if num >= tracker.next_number:
                        tracker.next_number = num + 1
                        tracker.save()
            except (ValueError, TypeError):
                pass  # Allow non-integer invoice numbers, but don't update tracker
        
        # Calculate totals unless skipped
        if not skip_calculation:
            self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        # Calculate subtotal from line items
        self.subtotal = sum(item.total for item in self.items.all())
        
        # Calculate tax
        self.tax_amount = (self.subtotal - self.discount_amount) * self.tax_rate
        
        # Calculate finance charge based on payment terms
        self.calculate_finance_charge()
        
        # Calculate total (including finance charge)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount + self.finance_charge
    
    def calculate_finance_charge(self):
        """Calculate finance charge based on customer payment terms and days past due"""
        from django.utils import timezone
        
        # Calculate days past due
        today = timezone.now().date()
        days_past_due = (today - self.due_date).days
        
        # Only apply finance charge if past due
        if days_past_due > 0:
            # Calculate finance charge (1.5% of the remaining balance)
            balance_due = self.subtotal + self.tax_amount - self.discount_amount - self.paid_amount
            if balance_due > 0:
                self.finance_charge = balance_due * Decimal('0.015')  # 1.5%
            else:
                self.finance_charge = Decimal('0.00')
        else:
            self.finance_charge = Decimal('0.00')
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        from django.utils import timezone
        return self.status == 'open' and self.due_date < timezone.now().date()
    
    @property
    def paid_amount(self):
        """Calculate total amount paid"""
        return self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.paid_amount


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
    
    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
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
    
    def __str__(self):
        return f"Payment {self.reference_number or self.id} - {self.customer.name} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        """Override save to update invoice status if needed"""
        super().save(*args, **kwargs)
        
        # Update invoice status if this payment covers the full amount
        if self.invoice:
            if self.invoice.balance_due <= 0:
                self.invoice.status = 'paid'
                self.invoice.save()

# Signal handlers to keep invoice totals up-to-date
def update_invoice_totals(invoice):
    invoice.calculate_totals()
    invoice.save(update_fields=[
        'subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'updated_at'
    ])

@receiver(post_save, sender=InvoiceItem)
def update_invoice_on_item_save(sender, instance, **kwargs):
    update_invoice_totals(instance.invoice)

@receiver(post_delete, sender=InvoiceItem)
def update_invoice_on_item_delete(sender, instance, **kwargs):
    update_invoice_totals(instance.invoice)
