from django.contrib import admin
from .models import Customer, Invoice, InvoiceItem, Payment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'current_balance', 'payment_terms', 'is_active', 'created_at']
    list_filter = ['is_active', 'payment_terms', 'created_at']
    search_fields = ['name', 'email', 'phone', 'tax_id']
    readonly_fields = ['id', 'current_balance', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Business Information', {
            'fields': ('tax_id', 'payment_terms', 'credit_limit')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['description', 'quantity', 'unit_price', 'total']
    readonly_fields = ['total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'issue_date', 'due_date', 'total_amount', 'status', 'balance_due']
    list_filter = ['status', 'issue_date', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['id', 'invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'balance_due', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]
    fieldsets = (
        ('Invoice Information', {
            'fields': ('customer', 'issue_date', 'due_date', 'status')
        }),
        ('Financial Information', {
            'fields': ('tax_rate', 'discount_amount', 'subtotal', 'tax_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'customer', 'invoice', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['reference_number', 'customer__name', 'invoice__invoice_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('customer', 'invoice', 'amount', 'payment_date', 'payment_method', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']
    list_filter = ['created_at']
    search_fields = ['description', 'invoice__invoice_number']
    readonly_fields = ['id', 'total', 'created_at', 'updated_at']
