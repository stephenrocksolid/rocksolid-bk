// payment_form.js: JS powering dynamic payment form

document.addEventListener('DOMContentLoaded', function() {
    const customerSelect = document.getElementById('id_customer');
    let lastInvoiceId = null; // Track the last selected invoice

    // When customer changes, fetch balance & invoice list
    customerSelect.addEventListener('change', function() {
        const customerId = this.value;
        if (!customerId) {
            document.getElementById('customer-balance-info').innerHTML = '';
            document.getElementById('invoice-select-wrapper').innerHTML = '<div class="col-md-6 mb-3" id="invoice-select-wrapper"><label for="id_invoice" class="form-label">Invoice (Optional)</label><select name="invoice" id="id_invoice" class="form-control"><option value="">---------</option></select><small class="form-text text-muted">Leave blank for general payment</small></div>';
            document.getElementById('invoice-balance-info').innerHTML = '';
            return;
        }
        // Balance sidebar
        htmx.ajax('GET', `/api/customer/${customerId}/balance/partial/`, {
            target: '#customer-balance-info', swap: 'innerHTML'
        });
        // Invoices dropdown select (full block)
        htmx.ajax('GET', `/api/customer/invoices/select/partial/?customer_id=${customerId}`, {
            target: '#invoice-select-wrapper', swap: 'outerHTML'
        });
    });

    // Use event delegation for invoice changes (works with dynamically loaded elements)
    document.addEventListener('change', function(event) {
        if (event.target && event.target.id === 'id_invoice') {
            console.log('Invoice changed:', event.target.value);
            const invoiceId = event.target.value;
            lastInvoiceId = invoiceId; // Save for afterSwap
            if (!invoiceId) {
                document.getElementById('invoice-balance-info').innerHTML = '';
                // Clear form fields when no invoice is selected
                document.getElementById('id_amount').value = '';
                return;
            }
            // Fetch invoice details and update sidebar
            htmx.ajax('GET', `/api/invoice/${invoiceId}/totals/partial/`, {
                target: '#invoice-balance-info', 
                swap: 'innerHTML'
            });
        }
    });

    // Listen for htmx:afterSwap to populate form fields after sidebar update
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.target && evt.target.id === 'invoice-balance-info' && lastInvoiceId) {
            console.log('Sidebar updated, now populating form fields');
            populateFormFields(lastInvoiceId);
        }
    });

    // Function to populate form fields with invoice data
    function populateFormFields(invoiceId) {
        console.log('Populating form fields for invoice:', invoiceId);
        // Fetch invoice data as JSON
        fetch(`/api/invoice/${invoiceId}/data/json/`)
            .then(response => {
                console.log('JSON response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Invoice data received:', data);
                // Set amount to balance due
                document.getElementById('id_amount').value = data.balance_due.toFixed(2);
                console.log('Amount set to:', data.balance_due.toFixed(2));
                // Set payment date to today
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('id_payment_date').value = today;
                console.log('Payment date set to:', today);
                // Set payment method to 'check'
                const paymentMethodSelect = document.getElementById('id_payment_method');
                if (paymentMethodSelect) {
                    paymentMethodSelect.value = 'check';
                    console.log('Payment method set to: check');
                } else {
                    console.log('Payment method select not found');
                }
            })
            .catch(error => {
                console.error('Error fetching invoice data:', error);
            });
    }

    // Pre-populate selects from URL params (customer / invoice)
    const urlParams = new URLSearchParams(window.location.search);
    const customerParam = urlParams.get('customer');
    const invoiceParam  = urlParams.get('invoice');
    if (customerParam) {
        customerSelect.value = customerParam;
        customerSelect.dispatchEvent(new Event('change'));
    }
    if (invoiceParam) {
        // Wait for invoice select to be loaded if customer was also specified
        setTimeout(() => {
            const invoiceSelect = document.getElementById('id_invoice');
            if (invoiceSelect) {
                invoiceSelect.value = invoiceParam;
                invoiceSelect.dispatchEvent(new Event('change'));
            }
        }, 500);
    }
}); 