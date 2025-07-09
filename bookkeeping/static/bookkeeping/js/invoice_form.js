// invoice_form.js: JS logic for dynamic invoice form

document.addEventListener('DOMContentLoaded', function() {
    const addItemBtn = document.getElementById('add-item-btn');
    const tbody = document.getElementById('invoice-items-tbody');
    const totalForms = document.getElementById('id_items-TOTAL_FORMS');
    const customerSelect = document.getElementById('id_customer');
    const dueDateInput = document.getElementById('id_due_date');
    const issueDateInput = document.getElementById('id_issue_date');
    const setTodayBtn = document.getElementById('set-today-btn');

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

        // Calculate finance charge if enabled
        calculateFinanceCharge(subtotal);

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

    // Calculate finance charge based on due date and enable checkbox
    function calculateFinanceCharge(subtotal) {
        const enableFinanceCharge = document.getElementById('id_enable_finance_charge');
        const financeChargeInput = document.getElementById('id_finance_charge');
        const dueDateInput = document.getElementById('id_due_date');
        const taxRate = parseFloat(document.getElementById('id_tax_rate').value) || 0;
        const discount = parseFloat(document.getElementById('id_discount_amount').value) || 0;
        const helpText = document.getElementById('finance-charge-help');

        if (!enableFinanceCharge || !financeChargeInput || !dueDateInput) return;

        if (enableFinanceCharge.checked) {
            const dueDate = new Date(dueDateInput.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Reset time to start of day
            
            const daysPastDue = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
            
            if (daysPastDue > 0) {
                // Calculate finance charge (1.5% of the remaining balance)
                const taxAmount = (subtotal - discount) * taxRate;
                const balanceDue = subtotal + taxAmount - discount;
                
                if (balanceDue > 0) {
                    const financeCharge = balanceDue * 0.015; // 1.5%
                    financeChargeInput.value = financeCharge.toFixed(2);
                    helpText.textContent = `Calculated automatically: ${daysPastDue} days past due (1.5% of balance)`;
                    helpText.className = 'form-text text-warning';
                } else {
                    financeChargeInput.value = '0.00';
                    helpText.textContent = 'No balance due - no finance charge applied';
                    helpText.className = 'form-text text-success';
                }
            } else {
                financeChargeInput.value = '0.00';
                const daysUntilDue = Math.abs(daysPastDue);
                helpText.textContent = `Invoice not yet due (${daysUntilDue} days until due)`;
                helpText.className = 'form-text text-info';
            }
        } else {
            financeChargeInput.value = '0.00';
            helpText.textContent = 'Finance charge disabled';
            helpText.className = 'form-text text-muted';
        }
    }

    // Initial listeners and calculation
    document.querySelectorAll('.quantity-input, .price-input').forEach(el => el.addEventListener('input', calculateItemTotals));
    document.getElementById('id_tax_rate').addEventListener('input', calculateItemTotals);
    document.getElementById('id_discount_amount').addEventListener('input', calculateItemTotals);
    document.getElementById('id_finance_charge').addEventListener('input', calculateItemTotals);
    
    // Add listeners for finance charge calculation
    const enableFinanceChargeCheckbox = document.getElementById('id_enable_finance_charge');
    
    if (enableFinanceChargeCheckbox) {
        enableFinanceChargeCheckbox.addEventListener('change', function() {
            const rows = tbody.getElementsByClassName('invoice-item-row');
            let subtotal = 0;
            Array.from(rows).forEach(row => {
                const qty = parseFloat(row.querySelector('.quantity-input').value) || 0;
                const price = parseFloat(row.querySelector('.price-input').value) || 0;
                subtotal += qty * price;
            });
            calculateFinanceCharge(subtotal);
            calculateItemTotals();
        });
    }
    
    // Add finance charge calculation to existing due date listener
    if (dueDateInput) {
        const originalChangeHandler = dueDateInput.onchange;
        dueDateInput.addEventListener('change', function() {
            const rows = tbody.getElementsByClassName('invoice-item-row');
            let subtotal = 0;
            Array.from(rows).forEach(row => {
                const qty = parseFloat(row.querySelector('.quantity-input').value) || 0;
                const price = parseFloat(row.querySelector('.price-input').value) || 0;
                subtotal += qty * price;
            });
            calculateFinanceCharge(subtotal);
            calculateItemTotals();
        });
    }
    
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

    // Listen for customer selection changes
    customerSelect.addEventListener('change', function() {
        updateDueDate();
        updateTerms();
    });

    // Also update when issue date changes (if customer is already selected)
    issueDateInput.addEventListener('change', function() {
        if (customerSelect.value) {
            updateDueDate();
        }
    });

    if (setTodayBtn && issueDateInput) {
        setTodayBtn.addEventListener('click', function() {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            issueDateInput.value = `${yyyy}-${mm}-${dd}`;
            // Trigger due date calculation
            if (customerSelect.value) {
                updateDueDate();
            }
        });
    }

    // Autofill Issue Date with today if empty (for new invoices)
    if (issueDateInput && !issueDateInput.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        issueDateInput.value = `${yyyy}-${mm}-${dd}`;
    }
}); 

function updateDueDate() {
    const customerId = customerSelect.value;
    const issueDate = issueDateInput.value;
    if (customerId && issueDate) {
        const url = `/api/customer/${customerId}/due-date/partial/?issue_date=${issueDate}`;
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const container = document.getElementById('due-date-container');
                if (container) {
                    container.innerHTML = html;
                }
            });
    }
}

function updateTerms() {
    const customerId = customerSelect.value;
    if (customerId) {
        const url = `/api/customer/${customerId}/terms/partial/`;
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const container = document.getElementById('terms-container');
                if (container) {
                    container.innerHTML = html;
                }
            });
    }
} 