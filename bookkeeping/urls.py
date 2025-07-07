from django.urls import path
from . import views

app_name = 'bookkeeping'

urlpatterns = [
    # Landing and Dashboard
    path('', views.home, name='home'),  # Legacy - redirects appropriately
    path('landing/', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Demo
    path('htmx-demo/', views.htmx_demo, name='htmx_demo'),
    path('button-click/', views.button_click, name='button_click'),
    
    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<uuid:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<uuid:customer_id>/edit/', views.customer_update, name='customer_update'),
    
    # Invoice URLs
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<uuid:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:invoice_id>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<uuid:invoice_id>/print/', views.invoice_print, name='invoice_print'),
    path('invoices/<uuid:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    
    # Payment URLs
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    
    # HTMX/AJAX endpoints
    path('api/customer/<uuid:customer_id>/balance/partial/', views.get_customer_balance_partial, name='get_customer_balance_partial'),
    path('api/customer/<uuid:customer_id>/invoices/partial/', views.get_customer_invoices_partial, name='get_customer_invoices_partial'),
    path('api/invoice/<uuid:invoice_id>/totals/partial/', views.get_invoice_totals_partial, name='get_invoice_totals_partial'),
    path('api/customer/<uuid:customer_id>/due-date/partial/', views.get_customer_due_date_partial, name='get_customer_due_date_partial'),
    path('api/customer/<uuid:customer_id>/terms/partial/', views.get_customer_terms_partial, name='get_customer_terms_partial'),
    path('api/invoice/calculate-totals/partial/', views.calculate_invoice_totals_partial, name='calculate_invoice_totals_partial'),
] 