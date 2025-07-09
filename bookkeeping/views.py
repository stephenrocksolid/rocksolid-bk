from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.forms import modelformset_factory
import random
from decimal import Decimal
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import urllib.parse

from .models import Customer, Invoice, InvoiceItem, Payment
from .forms import CustomerForm, InvoiceForm, InvoiceItemFormSet, PaymentForm


def landing_page(request):
    """Public landing page with RockSolid Data information"""
    return render(request, 'bookkeeping/landing.html')


@login_required
def dashboard(request):
    """Dashboard page with overview - requires login"""
    # Get summary statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_invoices = Invoice.objects.count()
    total_receivables = Invoice.objects.filter(
        status__in=['open', 'overdue']
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Recent activity
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('customer').order_by('-created_at')[:5]
    
    # Overdue invoices
    overdue_invoices = Invoice.objects.filter(
        status='open',
        due_date__lt=timezone.now().date()
    ).select_related('customer')[:5]
    
    context = {
        'total_customers': total_customers,
        'total_invoices': total_invoices,
        'total_receivables': total_receivables,
        'recent_invoices': recent_invoices,
        'recent_payments': recent_payments,
        'overdue_invoices': overdue_invoices,
    }
    return render(request, 'bookkeeping/dashboard.html', context)


# Legacy home view - redirect to dashboard for logged in users, landing page for others
def home(request):
    """Legacy home view - redirects appropriately"""
    if request.user.is_authenticated:
        return redirect('bookkeeping:dashboard')
    else:
        return redirect('bookkeeping:landing_page')


# Customer Views
@login_required
def customer_list(request):
    """List all customers with search and filtering"""
    customers = Customer.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        customers = customers.filter(is_active=True)
    elif status_filter == 'inactive':
        customers = customers.filter(is_active=False)
    
    # Sort options
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'balance':
        customers = sorted(customers, key=lambda x: x.current_balance, reverse=True)
    elif sort_by == 'recent':
        customers = customers.order_by('-created_at')
    else:
        customers = customers.order_by('name')
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    return render(request, 'bookkeeping/customer_list.html', context)


@login_required
def customer_detail(request, customer_id):
    """Show customer details with invoice and payment history"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Get customer's invoices
    invoices = customer.invoices.all().order_by('-issue_date')
    
    # Get customer's payments
    payments = customer.payments.all().order_by('-payment_date')
    
    # Calculate statistics
    total_invoiced = customer.invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    total_paid = customer.payments.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'customer': customer,
        'invoices': invoices,
        'payments': payments,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
    }
    return render(request, 'bookkeeping/customer_detail.html', context)


@login_required
def customer_create(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, f'Customer "{customer.name}" created successfully.')
            return redirect('bookkeeping:customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm()
    
    context = {'form': form, 'title': 'Add New Customer'}
    return render(request, 'bookkeeping/customer_form.html', context)


@login_required
def customer_update(request, customer_id):
    """Update an existing customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" updated successfully.')
            return redirect('bookkeeping:customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)
    
    context = {'form': form, 'customer': customer, 'title': f'Edit Customer: {customer.name}'}
    return render(request, 'bookkeeping/customer_form.html', context)


# Invoice Views
@login_required
def invoice_list(request):
    """List all invoices with filtering"""
    invoices = Invoice.objects.select_related('customer').all()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    # Filter by customer
    customer_filter = request.GET.get('customer', '')
    if customer_filter:
        invoices = invoices.filter(customer__name__icontains=customer_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        invoices = invoices.filter(issue_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(issue_date__lte=date_to)
    
    # Always sort by invoice_number descending
    invoices = invoices.order_by('-invoice_number')
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'customer_filter': customer_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': '-invoice_number',
    }
    return render(request, 'bookkeeping/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """Show invoice details"""
    invoice = get_object_or_404(Invoice.objects.select_related('customer'), id=invoice_id)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'bookkeeping/invoice_detail.html', context)


@login_required
def invoice_create(request):
    """Create a new invoice"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            
            # Save invoice items
            instances = formset.save(commit=False)
            for instance in instances:
                instance.invoice = invoice
                instance.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
            if request.POST.get('save_pdf') == '1':
                return render(request, 'bookkeeping/invoice_pdf_redirect.html', {
                    'invoice': invoice,
                })
            return redirect('bookkeeping:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet(prefix='items')
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Invoice'
    }
    return render(request, 'bookkeeping/invoice_form.html', context)


@login_required
def invoice_update(request, invoice_id):
    """Update an existing invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully.')
            return redirect('bookkeeping:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix='items')
    
    context = {
        'form': form,
        'formset': formset,
        'invoice': invoice,
        'title': f'Edit Invoice: {invoice.invoice_number}'
    }
    return render(request, 'bookkeeping/invoice_form.html', context)


@login_required
def invoice_print(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    context = {
        'invoice': invoice,
        'company_name': 'RockSolid Data Solutions',
        'company_address': 'PO Box 321, Perry, NY 14530',
        'company_email': 'accounting@rocksoliddata.solutions',
        'company_phone': '(620) 888 7050',
        'balance_due': invoice.balance_due,
        'total_payments': invoice.paid_amount,
        'finance_charge': invoice.finance_charge,
    }
    return render(request, 'bookkeeping/invoice_print.html', context)


@login_required
def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    context = {
        'invoice': invoice,
        'company_name': 'RockSolid Data Solutions',
        'company_address': 'PO Box 321, Perry, NY 14530',
        'company_email': 'accounting@rocksoliddata.solutions',
        'company_phone': '(620) 888 7050',
        'balance_due': invoice.balance_due,
        'total_payments': invoice.paid_amount,
        'finance_charge': invoice.finance_charge,
        'pdf_mode': True,
    }
    html_string = render_to_string('bookkeeping/invoice_print.html', context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    filename = f"Invoice {invoice.invoice_number} - {invoice.customer.name}.pdf"
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(filename)}"'
    return response


@login_required
def invoice_delete(request, invoice_id):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        # Check if invoice can be deleted (no payments made)
        if invoice.paid_amount > 0:
            messages.error(request, f'Cannot delete invoice {invoice.invoice_number} because payments have been made. Consider cancelling the invoice instead.')
            return redirect('bookkeeping:invoice_detail', invoice_id=invoice.id)
        
        # Store invoice number for success message
        invoice_number = invoice.invoice_number
        customer_name = invoice.customer.name
        
        # Delete the invoice
        invoice.delete()
        
        messages.success(request, f'Invoice {invoice_number} for {customer_name} has been deleted successfully.')
        return redirect('bookkeeping:invoice_list')
    
    # GET request - show confirmation page
    context = {
        'invoice': invoice,
        'title': f'Delete Invoice: {invoice.invoice_number}'
    }
    return render(request, 'bookkeeping/invoice_delete.html', context)


# Payment Views
@login_required
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.select_related('customer', 'invoice').all()
    
    # Filter by customer
    customer_filter = request.GET.get('customer', '')
    if customer_filter:
        payments = payments.filter(customer__name__icontains=customer_filter)
    
    # Filter by payment method
    method_filter = request.GET.get('method', '')
    if method_filter:
        payments = payments.filter(payment_method=method_filter)
    
    # Sort options
    sort_by = request.GET.get('sort', '-payment_date')
    payments = payments.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'customer_filter': customer_filter,
        'method_filter': method_filter,
        'sort_by': sort_by,
    }
    return render(request, 'bookkeeping/payment_list.html', context)


@login_required
def payment_create(request):
    """Create a new payment"""
    customer_id = request.GET.get('customer_id') or None
    invoices = Invoice.objects.none()
    if customer_id:
        invoices = Invoice.objects.filter(customer_id=customer_id, status__in=["open", "overdue"]).order_by('-issue_date')
    else:
        invoices = Invoice.objects.filter(status__in=["open", "overdue"]).order_by('-issue_date')

    if request.method == 'POST':
        form = PaymentForm(request.POST, invoice_queryset=invoices)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            # Check for overpayment
            overpayment = form.cleaned_data.get('overpayment', 0)
            if overpayment > 0:
                messages.warning(request, f'Payment recorded with ${overpayment:.2f} overpayment. This will be applied as a credit to the customer account.')
            else:
                messages.success(request, f'Payment of ${payment.amount} recorded successfully.')
            return redirect('bookkeeping:payment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentForm(invoice_queryset=invoices)

    context = {'form': form, 'title': 'Record Payment'}
    return render(request, 'bookkeeping/payment_form.html', context)


# HTMX Views for dynamic interactions
def htmx_demo(request):
    """HTMX demo page with dynamic button"""
    return render(request, 'bookkeeping/htmx_demo.html')


def button_click(request):
    """HTMX endpoint for button click"""
    if request.htmx:
        # Generate a random number for demo
        random_number = random.randint(1, 100)
        return HttpResponse(f'<p>Button clicked! Random number: {random_number}</p>')
    return HttpResponse('Invalid request')


# AJAX endpoints for dynamic data
@require_http_methods(["GET"])
@login_required
def get_customer_balance_partial(request, customer_id):
    """HTMX partial: customer balance sidebar"""
    customer = get_object_or_404(Customer, id=customer_id)
    html = render_to_string('bookkeeping/partials/customer_balance.html', {'customer': customer})
    return HttpResponse(html)


@require_http_methods(["GET"])
@login_required
def get_customer_invoices_partial(request, customer_id):
    """HTMX partial: <option> tags for invoice dropdown"""
    invoices = Invoice.objects.filter(customer_id=customer_id, status__in=["open", "overdue"]).order_by('-issue_date')
    html = render_to_string('bookkeeping/partials/invoice_options.html', {'invoices': invoices})
    return HttpResponse(html)


@require_http_methods(["GET"])
@login_required
def get_customer_invoices_select_partial(request):
    """HTMX partial: return invoice select for a given customer (open/overdue only)"""
    customer_id = request.GET.get('customer_id')
    invoices = Invoice.objects.none()
    if customer_id:
        invoices = Invoice.objects.filter(customer_id=customer_id, status__in=["open", "overdue"]).order_by('-issue_date')
    form = PaymentForm(invoice_queryset=invoices)
    context = {'form': form}
    return render(request, 'bookkeeping/partials/invoice_select.html', context)


@require_http_methods(["GET"])
@login_required
def get_invoice_totals_partial(request, invoice_id):
    """HTMX partial: invoice info sidebar"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    html = render_to_string('bookkeeping/partials/invoice_totals.html', {'invoice': invoice})
    return HttpResponse(html)


@require_http_methods(["POST"])
def calculate_invoice_totals_partial(request):
    """HTMX partial: calculate and return invoice totals"""
    # Get form data from request
    items_data = request.POST.getlist('items')
    tax_rate = float(request.POST.get('tax_rate', 0))
    discount_amount = float(request.POST.get('discount_amount', 0))
    
    subtotal = 0
    for item in items_data:
        quantity = float(item.get('quantity', 0))
        unit_price = float(item.get('unit_price', 0))
        subtotal += quantity * unit_price
    
    tax_amount = (subtotal - discount_amount) * (tax_rate / 100)
    total = subtotal + tax_amount - discount_amount
    
    html = render_to_string('bookkeeping/partials/invoice_totals_calc.html', {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': total
    })
    return HttpResponse(html)


@require_http_methods(["GET"])
@login_required
def get_customer_due_date_partial(request, customer_id):
    """HTMX partial: return due date based on customer payment terms and issue date"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Map payment terms to days
    payment_terms_days = {
        'net_15': 15,
        'net_30': 30,
        'net_60': 60,
        'net_90': 90,
        'due_on_receipt': 0,
    }
    
    # Get issue date from request
    issue_date_str = request.GET.get('issue_date', '')
    
    if issue_date_str:
        try:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
            days = payment_terms_days.get(customer.payment_terms, 30)
            due_date = issue_date + timedelta(days=days)
            due_date_str = due_date.strftime('%Y-%m-%d')
        except ValueError:
            due_date_str = ''
    else:
        due_date_str = ''
    
    html = render_to_string('bookkeeping/partials/due_date.html', {
        'due_date': due_date_str
    })
    return HttpResponse(html)


@require_http_methods(["GET"])
@login_required
def get_customer_terms_partial(request, customer_id):
    """HTMX partial: return customer terms for invoice"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Generate default terms based on payment terms
    payment_terms_map = {
        'net_15': 'Payment is due within 15 days of invoice date.',
        'net_30': 'Payment is due within 30 days of invoice date.',
        'net_60': 'Payment is due within 60 days of invoice date.',
        'net_90': 'Payment is due within 90 days of invoice date.',
        'due_on_receipt': 'Payment is due upon receipt of this invoice.',
    }
    base_terms = payment_terms_map.get(customer.payment_terms, 'Payment is due within 30 days of invoice date.')
    
    # Add finance charge information
    finance_charge_text = ' A 1.5% monthly finance charge will be applied to all balances past due.'
    terms = base_terms + finance_charge_text
    
    html = render_to_string('bookkeeping/partials/terms.html', {
        'terms': terms
    })
    return HttpResponse(html)


@require_http_methods(["GET"])
@login_required
def get_invoice_data_json(request, invoice_id):
    """Return invoice data as JSON for payment form auto-population"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    data = {
        'balance_due': float(invoice.balance_due),
        'total_amount': float(invoice.total_amount),
        'amount_paid': float(invoice.paid_amount),
        'subtotal': float(invoice.subtotal),
        'tax_amount': float(invoice.tax_amount),
        'invoice_number': invoice.invoice_number,
        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
    }
    return JsonResponse(data)
