/* =============================================================
   invoice_form.js  –  Pure static Alpine.js component.
   All Django context is provided by globals injected in the
   HTML template's inline <script> block:
     • CUSTOMERS_DATA   – { id: { name, phone, address, debt } }
     • CUSTOMERS_LIST   – [{ id, name, phone }]
     • PRODUCTS_DATA    – { id: { name, code, unit, description } }
     • INVOICE_INIT     – { discount, selectedCustomerId, items[] }
   ============================================================= */

/* ── Persian Datepicker init (no Django tags needed) ── */
document.addEventListener('DOMContentLoaded', function () {
    if (typeof $.fn.persianDatepicker === 'function') {
        $('.jalali-datepicker').persianDatepicker({
            format:       'YYYY/MM/DD',
            initialValue: true,
            autoClose:    true,
            calendar: {
                persian: { locale: 'fa' }
            }
        });
    }
});

/* ── Alpine.js component ── */
function invoiceForm() {
    return {

        /* ════════════════════════════════════════
           State
        ════════════════════════════════════════ */

        /* items */
        items:    [],
        discount: 0,

        /* customer searchable combobox */
        customerSearch:       '',
        selectedCustomerId:   '',
        selectedCustomerInfo: {},
        customerDropdownOpen: false,
        custHighlightIndex:   -1,

        /* customer modal */
        customerForm:   { id: null, name: '', phone: '', address: '' },
        customerErrors: {},
        customerSaving: false,

        /* product modal */
        productForm:      { id: null, name: '', unit: 'عدد', description: '', category: [] },
        productErrors:    {},
        productSaving:    false,
        _targetItemIndex: null,

        /* category management */
        newCategoryName:   '',
        categorySaving:    false,
        categoryErrors:    {},
        newCategoriesList: [],


        /* ════════════════════════════════════════
           Lifecycle
        ════════════════════════════════════════ */

        init() {
            /* ── Restore items from INVOICE_INIT (edit mode) ── */
            if (INVOICE_INIT.items && INVOICE_INIT.items.length) {
                this.items = INVOICE_INIT.items.map(it => ({
                    id:         it.id,
                    product:    it.product,
                    unit:       it.unit,
                    quantity:   it.quantity,
                    unit_price: it.unit_price,
                    total:      it.quantity * it.unit_price
                }));
            } else {
                this.items = [{ id: '', product: '', unit: '', quantity: 1, unit_price: 0, total: 0 }];
            }

            /* ── Restore discount ── */
            this.discount = INVOICE_INIT.discount || 0;

            this.updateManagementForm();

            /* ── Pre-select customer: URL param takes priority over form value ── */
            const urlParams = new URLSearchParams(window.location.search);
            const initialId = urlParams.get('customer') || INVOICE_INIT.selectedCustomerId;
            if (initialId) {
                const found = CUSTOMERS_LIST.find(c => String(c.id) === String(initialId));
                if (found) this.selectCustomer(found);
            }

            /* ── Watch discount input (Django-rendered field) ── */
            const discInput = document.querySelector('[name="discount"]');
            if (discInput) {
                discInput.addEventListener('input', e => {
                    this.discount = parseFloat(e.target.value) || 0;
                });
            }
        },


        /* ════════════════════════════════════════
           Customer – searchable combobox
        ════════════════════════════════════════ */

        get filteredCustomers() {
            const q = this.customerSearch.toLowerCase();
            if (!q) return CUSTOMERS_LIST;
            return CUSTOMERS_LIST.filter(c =>
                c.name.toLowerCase().includes(q) ||
                (c.phone && c.phone.includes(q))
            );
        },

        selectCustomer(c) {
            this.selectedCustomerId   = String(c.id);
            this.customerSearch       = c.name;
            this.customerDropdownOpen = false;
            this.custHighlightIndex   = -1;
            this._refreshCustomerInfo();
            /* keep hidden <select> in sync for Django POST */
            const sel = document.getElementById('id_customer');
            if (sel) sel.value = c.id;
        },

        custNavDown() {
            if (this.custHighlightIndex < this.filteredCustomers.length - 1)
                this.custHighlightIndex++;
        },

        custNavUp() {
            if (this.custHighlightIndex > 0)
                this.custHighlightIndex--;
        },

        custSelectHighlighted() {
            const c = this.filteredCustomers[this.custHighlightIndex];
            if (c) this.selectCustomer(c);
        },

        _refreshCustomerInfo() {
            this.selectedCustomerInfo = this.selectedCustomerId
                ? (CUSTOMERS_DATA[this.selectedCustomerId] || {})
                : {};
        },


        /* ════════════════════════════════════════
           Customer Modal
        ════════════════════════════════════════ */

        resetCustomerForm() {
            this.customerForm   = { id: null, name: '', phone: '', address: '' };
            this.customerErrors = {};
        },

        openAddCustomerModal() {
            this.resetCustomerForm();
            new bootstrap.Modal(document.getElementById('customerModal')).show();
        },

        openEditCustomerModal() {
            if (!this.selectedCustomerId) return;
            const d = CUSTOMERS_DATA[this.selectedCustomerId];
            if (!d) return;
            this.customerForm = {
                id:      this.selectedCustomerId,
                name:    d.name,
                phone:   d.phone,
                address: d.address
            };
            this.customerErrors = {};
            new bootstrap.Modal(document.getElementById('customerModal')).show();
        },

        saveCustomer() {
            this.customerErrors = {};
            if (!this.customerForm.name.trim()) {
                this.customerErrors.name = 'نام مشتری الزامی است.';
                return;
            }
            this.customerSaving = true;

            const url = this.customerForm.id
                ? `/api/customers/${this.customerForm.id}/edit/`
                : '/api/customers/add/';

            fetch(url, {
                method:  'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken':  document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(this.customerForm)
            })
            .then(r => r.json())
            .then(data => {
                this.customerSaving = false;
                if (data.success) {
                    const c = data.customer;
                    /* update local lookup */
                    CUSTOMERS_DATA[c.id] = {
                        name:    c.name,
                        phone:   c.phone    || '',
                        address: c.address  || '',
                        debt:    c.debt     || 0
                    };
                    if (!this.customerForm.id) {
                        /* new customer – add to list and hidden select */
                        CUSTOMERS_LIST.push({ id: String(c.id), name: c.name, phone: c.phone || '' });
                        const sel = document.getElementById('id_customer');
                        if (sel) sel.add(new Option(c.name, c.id));
                    } else {
                        /* edited – update existing list entry */
                        const existing = CUSTOMERS_LIST.find(x => String(x.id) === String(c.id));
                        if (existing) { existing.name = c.name; existing.phone = c.phone || ''; }
                    }
                    this.selectCustomer({ id: String(c.id), name: c.name, phone: c.phone || '' });
                    bootstrap.Modal.getInstance(document.getElementById('customerModal')).hide();
                } else {
                    this.customerErrors.general = data.error || 'خطا در ذخیره اطلاعات.';
                }
            })
            .catch(() => {
                this.customerSaving = false;
                this.customerErrors.general = 'خطا در ارتباط با سرور.';
            });
        },


        /* ════════════════════════════════════════
           Product Modal
        ════════════════════════════════════════ */

        openAddProductModal(itemIndex) {
            this._targetItemIndex = itemIndex;
            this.productForm      = { id: null, name: '', unit: 'عدد', description: '', category: [] };
            this.productErrors    = {};
            this.newCategoryName  = '';
            this.categoryErrors   = {};
            new bootstrap.Modal(document.getElementById('productModal')).show();
        },

        openEditProductModal(itemIndex) {
            const pid = this.items[itemIndex].product;
            if (!pid) return;
            const d = PRODUCTS_DATA[pid];
            if (!d) return;
            this._targetItemIndex = itemIndex;
            this.productForm      = { id: pid, name: d.name, unit: d.unit, description: d.description, category: [] };
            this.productErrors    = {};
            this.newCategoryName  = '';
            this.categoryErrors   = {};
            new bootstrap.Modal(document.getElementById('productModal')).show();
        },

        saveProduct() {
            this.productErrors = {};
            if (!this.productForm.name.trim()) {
                this.productErrors.name = 'نام کالا الزامی است.';
                return;
            }
            this.productSaving = true;

            const url = this.productForm.id
                ? `/api/products/${this.productForm.id}/edit/`
                : '/api/products/add/';

            fetch(url, {
                method:  'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken':  document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(this.productForm)
            })
            .then(r => r.json())
            .then(data => {
                this.productSaving = false;
                if (data.success) {
                    const p = data.product;
                    /* update local lookup */
                    PRODUCTS_DATA[p.id] = {
                        name:        p.name,
                        code:        p.code        || '',
                        unit:        p.unit,
                        description: p.description || ''
                    };
                    /* update every product <select> in the items table */
                    document.querySelectorAll('select[name$="-product"]').forEach(sel => {
                        let opt = sel.querySelector(`option[value="${p.id}"]`);
                        if (!opt) {
                            opt = new Option(p.name, p.id);
                            sel.add(opt);
                        } else {
                            opt.text = p.name;
                        }
                        opt.dataset.unit = p.unit;
                        opt.dataset.code = p.code || '';
                    });
                    /* auto-select the new/edited product in the target row */
                    if (this._targetItemIndex !== null) {
                        this.items[this._targetItemIndex].product = String(p.id);
                        this.items[this._targetItemIndex].unit    = p.unit;
                        this.$nextTick(() => {
                            const sel = document.querySelectorAll('select[name$="-product"]')[this._targetItemIndex];
                            if (sel) sel.value = p.id;
                        });
                    }
                    bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
                } else {
                    this.productErrors.general = data.error || 'خطا در ذخیره اطلاعات.';
                }
            })
            .catch(() => {
                this.productSaving = false;
                this.productErrors.general = 'خطا در ارتباط با سرور.';
            });
        },


        /* ════════════════════════════════════════
           Category management (inside product modal)
        ════════════════════════════════════════ */

        getCategoryName(id) {
            /* check session-created categories first */
            const fresh = this.newCategoriesList.find(c => String(c.id) === String(id));
            if (fresh) return fresh.name;
            /* fall back to the server-rendered <select> */
            const opt = document.querySelector(`#catSelect option[value="${id}"]`);
            return opt ? opt.textContent.trim() : String(id);
        },

        addCategoryFromSelect(event) {
            const val = event.target.value;
            if (!val) return;
            if (!this.productForm.category.includes(val))
                this.productForm.category.push(val);
            event.target.value = ''; /* reset dropdown to placeholder */
        },

        removeCategoryTag(id) {
            this.productForm.category = this.productForm.category.filter(c => c !== id);
        },

        /* ════════════════════════════════════════
           Invoice items
        ════════════════════════════════════════ */

        addItem() {
            this.items.push({ id: '', product: '', unit: '', quantity: 1, unit_price: 0, total: 0 });
            this.updateManagementForm();
        },

        removeItem(index) {
            if (this.items.length > 1) {
                this.items.splice(index, 1);
                this.updateManagementForm();
            }
        },

        onProductChange(index) {
            const sel = document.querySelectorAll('select[name$="-product"]')[index];
            if (sel) {
                const opt = sel.options[sel.selectedIndex];
                this.items[index].unit = opt ? (opt.dataset.unit || '') : '';
            }
            this.updateItemTotal(index);
        },

        updateItemTotal(index) {
            const it  = this.items[index];
            it.total  = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0);
        },


        /* ════════════════════════════════════════
           Computed totals
        ════════════════════════════════════════ */

        get subtotal() {
            return this.items.reduce((sum, it) => sum + (parseFloat(it.total) || 0), 0);
        },

        get total() {
            return Math.max(0, this.subtotal - (parseFloat(this.discount) || 0));
        },


        /* ════════════════════════════════════════
           Helpers
        ════════════════════════════════════════ */

        formatNumber(v) {
            return new Intl.NumberFormat('fa-IR').format(parseFloat(v) || 0);
        },

        updateManagementForm() {
            this.$nextTick(() => {
                const tf = document.querySelector('input[name="items-TOTAL_FORMS"]');
                if (tf) tf.value = this.items.length;
            });
        },

        validateForm(event) {
            if (!this.selectedCustomerId) {
                event.preventDefault();
                alert('لطفاً یک مشتری انتخاب کنید.');
                return false;
            }
            if (!this.items.length) {
                event.preventDefault();
                alert('حداقل یک قلم کالا باید وارد شود.');
                return false;
            }
            for (let i = 0; i < this.items.length; i++) {
                const it = this.items[i];
                if (!it.product) {
                    event.preventDefault();
                    alert('کالا در ردیف ' + (i + 1) + ' انتخاب نشده است.');
                    return false;
                }
                if (!it.quantity || parseFloat(it.quantity) <= 0) {
                    event.preventDefault();
                    alert('تعداد ردیف ' + (i + 1) + ' نامعتبر است.');
                    return false;
                }
                if (parseFloat(it.unit_price) < 0) {
                    event.preventDefault();
                    alert('بهای واحد در ردیف ' + (i + 1) + ' نامعتبر است.');
                    return false;
                }
            }
            return true;
        }

    };
}