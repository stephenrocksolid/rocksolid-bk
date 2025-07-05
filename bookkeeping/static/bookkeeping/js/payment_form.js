// payment_form.js: JS powering dynamic payment form

document.addEventListener('DOMContentLoaded', function() {
    const customerSelect = document.getElementById('id_customer');
    const invoiceSelect  = document.getElementById('id_invoice');

    // When customer changes, fetch balance & invoice list
    customerSelect.addEventListener('change', function() {
        const customerId = this.value;
        if (!customerId) {
            document.getElementById('customer-balance-info').innerHTML = '';
            invoiceSelect.innerHTML = '<option value="">---------</option>';
            document.getElementById('invoice-balance-info').innerHTML = '';
            return;
        }
        // Balance sidebar
        htmx.ajax('GET', `/api/customer/${customerId}/balance/partial/`, {
            target: '#customer-balance-info', swap: 'innerHTML'
        });
        // Invoices dropdown options
        htmx.ajax('GET', `/api/customer/${customerId}/invoices/partial/`, {
            target: '#id_invoice', swap: 'outerHTML'
        });
    });

    // When invoice changes, fetch sidebar totals
    invoiceSelect.addEventListener('change', function() {
        const invoiceId = this.value;
        if (!invoiceId) {
            document.getElementById('invoice-balance-info').innerHTML = '';
            return;
        }
        htmx.ajax('GET', `/api/invoice/${invoiceId}/totals/partial/`, {
            target: '#invoice-balance-info', swap: 'innerHTML'
        });
    });

    // Pre-populate selects from URL params (customer / invoice)
    const urlParams = new URLSearchParams(window.location.search);
    const customerParam = urlParams.get('customer');
    const invoiceParam  = urlParams.get('invoice');
    if (customerParam) {
        customerSelect.value = customerParam;
        customerSelect.dispatchEvent(new Event('change'));
    }
    if (invoiceParam) {
        invoiceSelect.value = invoiceParam;
        invoiceSelect.dispatchEvent(new Event('change'));
    }
}); 