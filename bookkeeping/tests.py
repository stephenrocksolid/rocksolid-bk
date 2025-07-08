from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from .models import Customer, Invoice, InvoiceItem, Payment
from django.db import models


class CustomerBalanceTestCase(TestCase):
    """Test cases for customer balance calculation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@example.com',
            created_by=self.user
        )
    
    def test_current_balance_with_no_invoices(self):
        """Test balance calculation when customer has no invoices"""
        self.assertEqual(self.customer.current_balance, Decimal('0.00'))
    
    def test_current_balance_with_unpaid_invoice(self):
        """Test balance calculation with one unpaid invoice"""
        # Create an invoice
        invoice = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice.save(skip_calculation=True)
        
        # Balance should be the invoice amount
        self.assertEqual(self.customer.current_balance, Decimal('100.00'))
    
    def test_current_balance_with_partial_payment(self):
        """Test balance calculation with partial payment"""
        # Create an invoice
        invoice = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice.save(skip_calculation=True)
        
        # Create a partial payment
        Payment.objects.create(
            customer=self.customer,
            invoice=invoice,
            amount=Decimal('60.00'),
            payment_date=timezone.now().date(),
            payment_method='check',
            created_by=self.user
        )
        invoice.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal('40.00'))
    
    def test_current_balance_with_full_payment(self):
        """Test balance calculation with full payment"""
        # Create an invoice
        invoice = Invoice.objects.create(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            created_by=self.user
        )
        # Update total_amount directly without triggering save() logic
        invoice.total_amount = Decimal('100.00')
        invoice.save(update_fields=['total_amount'])
        
        # Create a full payment
        Payment.objects.create(
            customer=self.customer,
            invoice=invoice,
            amount=Decimal('100.00'),
            payment_date=timezone.now().date(),
            payment_method='check',
            created_by=self.user
        )
        
        # Debug output
        total_invoiced = self.customer.invoices.exclude(status='cancelled').aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        total_payments = self.customer.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        print(f"DEBUG: total_invoiced={total_invoiced}, total_payments={total_payments}")
        
        self.assertEqual(self.customer.current_balance, Decimal('0.00'))
    
    def test_current_balance_with_multiple_invoices(self):
        """Test balance calculation with multiple invoices"""
        # Create first invoice
        invoice1 = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice1.save(skip_calculation=True)
        
        # Create second invoice
        invoice2 = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            total_amount=Decimal('200.00'),
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice2.save(skip_calculation=True)
        
        # Create payment for first invoice
        Payment.objects.create(
            customer=self.customer,
            invoice=invoice1,
            amount=Decimal('100.00'),
            payment_date=timezone.now().date(),
            payment_method='check',
            created_by=self.user
        )
        invoice1.refresh_from_db()
        invoice2.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal('200.00'))
    
    def test_current_balance_with_cancelled_invoice(self):
        """Test balance calculation excludes cancelled invoices"""
        # Create a cancelled invoice
        invoice = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='cancelled',
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice.save(skip_calculation=True)
        
        # Balance should be zero (cancelled invoices excluded)
        self.assertEqual(self.customer.current_balance, Decimal('0.00'))
    
    def test_current_balance_with_overpayment(self):
        """Test balance calculation with overpayment"""
        # Create an invoice
        invoice = Invoice(
            customer=self.customer,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='open',
            total_amount=Decimal('100.00'),
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            finance_charge=Decimal('0.00'),
            created_by=self.user
        )
        invoice.save(skip_calculation=True)
        
        # Create an overpayment
        Payment.objects.create(
            customer=self.customer,
            invoice=invoice,
            amount=Decimal('120.00'),
            payment_date=timezone.now().date(),
            payment_method='check',
            created_by=self.user
        )
        invoice.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal('-20.00'))
