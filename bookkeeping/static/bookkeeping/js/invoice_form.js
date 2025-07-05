// invoice_form.js: JS logic for dynamic invoice form

document.addEventListener('DOMContentLoaded', function() {
    const addItemBtn = document.getElementById('add-item-btn');
    const tbody = document.getElementById('invoice-items-tbody');
    const totalForms = document.getElementById('id_items-TOTAL_FORMS');
    const customerSelect = document.getElementById('id_customer');
    const dueDateInput = document.getElementById('id_due_date');
    const issueDateInput = document.getElementById('id_issue_date');

    // Add new item row to the table
    addItemBtn.addEventListener('click', function() {
        const newFormNum = parseInt(totalForms.value);
        const newRow = document.createElement('tr');
        newRow.className = 'invoice-item-row';
        newRow.innerHTML = `
            <td><input type="text" name="items-${newFormNum}-description" class="form-control" placeholder="Item description"></td>
            <td><input type="number" name="items-${newFormNum}-quantity" class="form-control quantity-input" step="0.01" min="0.01"></td>
            <td><input type="number" name="items-${newFormNum}-unit_price" class="form-control price-input" step="0.01" min="0"></td>
            <td><span class="item-total">$0.00</span></td>
            <td class="text-center">
                <button type="button" class="btn btn-outline-danger btn-lg delete-item-btn" title="Delete Item" style="font-size: 2rem; padding: 1rem 1.5rem;">
                    <i class="fas fa-trash"></i>
                </button>
                <input type="checkbox" name="items-${newFormNum}-DELETE" style="display: none;">
            </td>`;
        console.log('Added new item row with no default values');
        tbody.appendChild(newRow);
        totalForms.value = newFormNum + 1;

        // Attach listeners to new inputs
        newRow.querySelector('.quantity-input').addEventListener('input', calculateItemTotals);
        newRow.querySelector('.price-input').addEventListener('input', calculateItemTotals);
        
        // Attach delete button listener
        newRow.querySelector('.delete-item-btn').addEventListener('click', function() {
            deleteItemRow(newRow);
        });
    });

    // Delete item row function
    function deleteItemRow(row) {
        // Mark the DELETE checkbox as checked
        const deleteCheckbox = row.querySelector('input[name*="-DELETE"]');
        if (deleteCheckbox) {
            deleteCheckbox.checked = true;
        }
        
        // Hide the row with a fade effect
        row.style.transition = 'opacity 0.3s ease-out';
        row.style.opacity = '0';
        
        setTimeout(() => {
            row.style.display = 'none';
            calculateItemTotals(); // Recalculate totals after deletion
        }, 300);
    }

    // Calculate and display item totals
    function calculateItemTotals() {
        const rows = tbody.getElementsByClassName('invoice-item-row');
        let subtotal = 0;
        Array.from(rows).forEach(row => {
            const qty = parseFloat(row.querySelector('.quantity-input').value) || 0;
            const price = parseFloat(row.querySelector('.price-input').value) || 0;
            const total = qty * price;
            row.querySelector('.item-total').textContent = '$' + total.toFixed(2);
            subtotal += total;
        });

        // Update sidebar figures
        const taxRate = parseFloat(document.getElementById('id_tax_rate').value) || 0;
        const discount = parseFloat(document.getElementById('id_discount_amount').value) || 0;
        const financeCharge = parseFloat(document.getElementById('id_finance_charge').value) || 0;
        const taxAmount = (subtotal - discount) * taxRate;
        const grandTotal = subtotal + taxAmount - discount + financeCharge;

        document.getElementById('subtotal-display').textContent = '$' + subtotal.toFixed(2);
        document.getElementById('tax-display').textContent    = '$' + taxAmount.toFixed(2);
        document.getElementById('total-display').textContent  = '$' + grandTotal.toFixed(2);
    }

    // Initial listeners and calculation
    document.querySelectorAll('.quantity-input, .price-input').forEach(el => el.addEventListener('input', calculateItemTotals));
    document.getElementById('id_tax_rate').addEventListener('input', calculateItemTotals);
    document.getElementById('id_discount_amount').addEventListener('input', calculateItemTotals);
    document.getElementById('id_finance_charge').addEventListener('input', calculateItemTotals);
    
    // Hide existing DELETE checkboxes and add delete button listeners
    document.querySelectorAll('input[name*="-DELETE"]').forEach(checkbox => {
        checkbox.style.display = 'none';
    });
    
    // Add delete button listeners to existing rows
    document.querySelectorAll('.delete-item-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const row = this.closest('.invoice-item-row');
            deleteItemRow(row);
        });
    });
    
    calculateItemTotals();

    // Customer / Issue-date change triggers payment-terms HTMX request
    function refreshPaymentTerms() {
        const customerId = customerSelect.value;
        if (!customerId) return;
        const issueDate = issueDateInput.value;
        const url = `/api/customer/${customerId}/payment-terms/partial/?issue_date=${issueDate}`;
        htmx.ajax('GET', url, { target: '#payment-terms-container', swap: 'innerHTML' });
    }

    customerSelect.addEventListener('change', refreshPaymentTerms);
    issueDateInput.addEventListener('change', refreshPaymentTerms);
}); 