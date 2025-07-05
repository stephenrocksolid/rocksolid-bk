from django import forms
from django.forms import ModelForm, inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import Customer, Invoice, InvoiceItem, Payment


class CustomerForm(ModelForm):
    """Form for creating and editing customers"""
    
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'state', 
            'zip_code', 'country', 'tax_id', 'payment_terms', 
            'credit_limit', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company or individual name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP/Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tax ID or Business Number'}),
            'payment_terms': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Additional notes about this customer'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_credit_limit(self):
        """Validate credit limit is not negative"""
        credit_limit = self.cleaned_data.get('credit_limit')
        if credit_limit and credit_limit < 0:
            raise ValidationError('Credit limit cannot be negative.')
        return credit_limit


class InvoiceForm(ModelForm):
    """Form for creating and editing invoices"""
    
    class Meta:
        model = Invoice
        fields = [
            'customer', 'issue_date', 'due_date', 'status', 
            'tax_rate', 'discount_amount', 'finance_charge', 'notes', 'terms'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': '0', 'max': '1'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'finance_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Invoice notes'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment terms and conditions'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default dates
        if not self.instance.pk:
            self.fields['issue_date'].initial = timezone.now().date()
            # Default due date based on customer payment terms (30 days if no customer selected)
            self.fields['due_date'].initial = (timezone.now() + timezone.timedelta(days=30)).date()
            self.fields['tax_rate'].initial = Decimal('0.08')  # 8% default tax rate
    
    def clean(self):
        """Validate invoice dates and amounts"""
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        discount_amount = cleaned_data.get('discount_amount', Decimal('0.00'))
        finance_charge = cleaned_data.get('finance_charge', Decimal('0.00'))
        
        if issue_date and due_date and issue_date > due_date:
            raise ValidationError('Due date must be after or equal to issue date.')
        
        if discount_amount and discount_amount < 0:
            raise ValidationError('Discount amount cannot be negative.')
        
        if finance_charge and finance_charge < 0:
            raise ValidationError('Finance charge cannot be negative.')
        
        return cleaned_data


class InvoiceItemForm(ModelForm):
    """Form for individual invoice items"""
    
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01', 'min': '0'}),
        }
    
    def clean_quantity(self):
        """Validate quantity is positive"""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        return quantity
    
    def clean_unit_price(self):
        """Validate unit price is not negative"""
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price and unit_price < 0:
            raise ValidationError('Unit price cannot be negative.')
        return unit_price


# Create formset for invoice items
InvoiceItemFormSet = inlineformset_factory(
    Invoice, 
    InvoiceItem, 
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    fields=['description', 'quantity', 'unit_price']
)


class PaymentForm(ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = ['customer', 'invoice', 'amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'invoice': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Check number, transaction ID, etc.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default payment date and method
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()
            self.fields['payment_method'].initial = 'check'  # Default to check
        
        # Filter invoices to only show unpaid ones
        self.fields['invoice'].queryset = Invoice.objects.filter(
            status__in=['open', 'overdue']
        ).select_related('customer')
    
    def clean_amount(self):
        """Validate payment amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Payment amount must be greater than zero.')
        return amount
    
    def clean(self):
        """Validate payment against invoice if specified"""
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        
        if invoice and amount:
            # Check if payment amount exceeds invoice balance
            if amount > invoice.balance_due:
                # Allow overpayment but show a warning
                cleaned_data['overpayment'] = amount - invoice.balance_due
        
        return cleaned_data


# Search and Filter Forms
class CustomerSearchForm(forms.Form):
    """Form for customer search and filtering"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search customers...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses'), ('active', 'Active'), ('inactive', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('name', 'Name'),
            ('balance', 'Balance'),
            ('recent', 'Recently Added')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class InvoiceSearchForm(forms.Form):
    """Form for invoice search and filtering"""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Invoice.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    customer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by customer...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('-issue_date', 'Issue Date (Newest)'),
            ('issue_date', 'Issue Date (Oldest)'),
            ('-total_amount', 'Amount (Highest)'),
            ('total_amount', 'Amount (Lowest)'),
            ('-due_date', 'Due Date (Newest)'),
            ('due_date', 'Due Date (Oldest)'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    ) 