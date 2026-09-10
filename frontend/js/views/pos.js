// ==============================================================================
// Inventory Management AI: POS Billing Terminal & Thermal Receipt Controller
// Modern Light SaaS Terminal with Split GST & UPI QR Generator
// ==============================================================================

const POSView = {
  cart: [],
  selectedPayment: 'CASH',
  products: [],
  activeCategory: '',

  async render(container) {
    this.cart = [];
    this.selectedPayment = 'CASH';
    this.activeCategory = '';

    container.innerHTML = `
      <div class="pos-container">
        <!-- Left Panel: Product Catalog & Search -->
        <div class="pos-catalog-panel">
          <div class="pos-search-bar">
            <div class="search-input-wrap" style="flex: 1;">
              <span class="icon">🔍</span>
              <input type="text" id="pos-search-input" class="form-control" placeholder="Search product name, Tamil name, or scan barcode..." autofocus />
            </div>
            <div class="barcode-badge-indicator">
              <span>⚡ BARCODE SCANNER ACTIVE</span>
            </div>
          </div>

          <!-- Category Chips -->
          <div class="pos-category-chips" id="pos-category-chips">
            <div class="cat-chip active" data-cat="">🌟 All Items</div>
            <div class="cat-chip" data-cat="Rice & Grains">🍚 Rice & Grains</div>
            <div class="cat-chip" data-cat="Cooking Oils">🛢️ Cooking Oils</div>
            <div class="cat-chip" data-cat="Salt & Sugar">🧂 Salt & Sugar</div>
            <div class="cat-chip" data-cat="Atta & Flours">🌾 Atta & Flours</div>
            <div class="cat-chip" data-cat="Spices & Masalas">🌶️ Spices & Masalas</div>
            <div class="cat-chip" data-cat="Dairy & Fresh">🥛 Dairy & Fresh</div>
            <div class="cat-chip" data-cat="Cleaning & Detergents">🧼 Cleaning & Detergents</div>
            <div class="cat-chip" data-cat="Biscuits & Snacks">🍪 Biscuits & Snacks</div>
          </div>

          <!-- Product Grid -->
          <div class="pos-product-grid" id="pos-product-grid">
            <p style="color: var(--text-muted); font-size: 0.85rem;">Loading catalog...</p>
          </div>
        </div>

        <!-- Right Panel: Active Cart & Billing Terminal -->
        <div class="pos-cart-panel">
          <div class="cart-header">
            <div class="cart-title">
              <span>🧾 Active Cart</span>
              <span class="cart-item-count" id="cart-count">0 items</span>
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-clear-cart" title="Clear Cart">Clear</button>
          </div>

          <!-- Cart Line Items List -->
          <div class="cart-items-list" id="cart-items-list">
            <div style="text-align: center; color: var(--text-muted); margin-top: 3.5rem; font-size: 0.85rem;">
              <div style="font-size: 2.5rem; margin-bottom: 0.5rem; opacity: 0.5;">🛒</div>
              Scan barcode or click items to add to cart
            </div>
          </div>

          <!-- Customer details input -->
          <div style="padding: 0.6rem 1rem; border-top: 1px solid var(--border-color); display: flex; gap: 0.5rem; background: #F8FAFC;">
            <input type="text" id="cust-name-input" class="form-control" style="font-size: 0.775rem; padding: 0.4rem 0.6rem;" placeholder="Customer (Default: Walk-in)" />
            <input type="text" id="cust-phone-input" class="form-control" style="font-size: 0.775rem; padding: 0.4rem 0.6rem;" placeholder="Phone (Optional)" />
          </div>

          <!-- Bill Financial Summary -->
          <div class="cart-summary">
            <div class="summary-line">
              <span>Subtotal (Base Value):</span>
              <span id="cart-subtotal">₹0.00</span>
            </div>
            <div class="summary-line">
              <span>CGST (Central Tax):</span>
              <span id="cart-cgst">₹0.00</span>
            </div>
            <div class="summary-line">
              <span>SGST (Tamil Nadu Tax):</span>
              <span id="cart-sgst">₹0.00</span>
            </div>
            <div class="summary-line">
              <span>Total GST:</span>
              <span id="cart-total-gst" style="color: #D97706; font-weight: 700;">₹0.00</span>
            </div>
            <div class="summary-line total-line">
              <span>Grand Total:</span>
              <span id="cart-grand-total" style="color: #0F172A;">₹0.00</span>
            </div>
          </div>

          <!-- Payment Options -->
          <div class="cart-payment-methods">
            <button class="pay-btn active" data-method="CASH">
              <span style="font-size: 1.1rem;">💵</span> Cash
            </button>
            <button class="pay-btn" data-method="UPI">
              <span style="font-size: 1.1rem;">📱</span> UPI / GPay
            </button>
            <button class="pay-btn" data-method="DEBIT_CARD">
              <span style="font-size: 1.1rem;">💳</span> Card
            </button>
            <button class="pay-btn" data-method="CREDIT">
              <span style="font-size: 1.1rem;">📒</span> Khata
            </button>
          </div>

          <button id="btn-checkout" class="btn btn-ai cart-checkout-btn" disabled>
            <span>💳</span> Complete Billing &rarr;
          </button>
        </div>
      </div>
    `;

    this.setupListeners();
    await this.loadInitialData();
  },

  setupListeners() {
    const searchInput = document.getElementById('pos-search-input');
    let timer = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => this.filterAndRenderGrid(), 180);
    });

    // Barcode scanner Enter key handler
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = searchInput.value.trim();
        const matched = this.products.find(p => (p.barcode && p.barcode === query) || p.name.toLowerCase() === query.toLowerCase());
        if (matched) {
          this.addToCart(matched);
          searchInput.value = '';
          this.filterAndRenderGrid();
        }
      }
    });

    document.getElementById('btn-clear-cart').addEventListener('click', () => {
      this.cart = [];
      this.renderCart();
    });

    document.querySelectorAll('.pay-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.pay-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.selectedPayment = btn.getAttribute('data-method');
      });
    });

    document.getElementById('btn-checkout').addEventListener('click', () => {
      this.handleCheckout();
    });
  },

  async loadInitialData() {
    try {
      const [catRes, prodRes] = await Promise.all([
        API.get('/api/products/categories'),
        API.get('/api/products', { limit: 200 })
      ]);

      this.products = prodRes.items || [];

      // Render category chips
      const chipsContainer = document.getElementById('pos-category-chips');
      if (chipsContainer && catRes) {
        chipsContainer.innerHTML = `<div class="cat-chip active" data-cat="">🌟 All Items</div>` +
          catRes.map(c => `<div class="cat-chip" data-cat="${c.id}">${c.name}</div>`).join('');

        chipsContainer.querySelectorAll('.cat-chip').forEach(chip => {
          chip.addEventListener('click', () => {
            chipsContainer.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            this.activeCategory = chip.getAttribute('data-cat');
            this.filterAndRenderGrid();
          });
        });
      }

      this.filterAndRenderGrid();
    } catch (e) {
      console.error('Failed loading POS data', e);
    }
  },

  filterAndRenderGrid() {
    const grid = document.getElementById('pos-product-grid');
    if (!grid) return;

    const searchVal = document.getElementById('pos-search-input')?.value.toLowerCase().trim() || '';

    let list = this.products;
    if (this.activeCategory) {
      list = list.filter(p => p.category_id == this.activeCategory || p.category_name == this.activeCategory);
    }
    if (searchVal) {
      list = list.filter(p =>
        p.name.toLowerCase().includes(searchVal) ||
        (p.tamil_name && p.tamil_name.includes(searchVal)) ||
        (p.barcode && p.barcode.includes(searchVal))
      );
    }

    if (list.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
          No items found in this category or search.
        </div>
      `;
      return;
    }

    grid.innerHTML = list.map(p => {
      const stockHealth = Math.min(100, Math.round((p.current_stock / (p.reorder_point * 2 || 20)) * 100));
      const fillClass = p.current_stock <= p.reorder_point ? 'fill-critical' : (p.current_stock <= p.reorder_point * 1.5 ? 'fill-warning' : 'fill-safe');

      return `
        <div class="pos-item-card" onclick="POSView.addToCartById(${p.id})">
          <div class="pos-item-img">
            ${Assets.getProductImage(p.name, p.category_name || '')}
          </div>
          <div class="pos-item-name">${p.name}</div>
          <div class="pos-item-tamil">${p.tamil_name || ''}</div>
          <div class="pos-item-footer">
            <div style="flex: 1;">
              <div class="pos-item-price">${formatINR(p.selling_price)}</div>
              <div class="pos-item-stock-tag">Stock: ${p.current_stock} ${p.unit}</div>
              <div class="stock-health-bar-wrap" style="max-width: 80px;">
                <div class="stock-health-bar-fill ${fillClass}" style="width: ${stockHealth}%;"></div>
              </div>
            </div>
            <button class="btn btn-primary btn-sm" style="padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.75rem;">
              + Add
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  addToCartById(prodId) {
    const prod = this.products.find(p => p.id === prodId);
    if (prod) this.addToCart(prod);
  },

  addToCart(prod) {
    if (prod.current_stock <= 0) {
      showToast(`Out of stock! Cannot sell ${prod.name}`, 'error');
      return;
    }

    const existing = this.cart.find(it => it.product_id === prod.id);
    if (existing) {
      if (existing.quantity >= prod.current_stock) {
        showToast(`Cannot add more than available shelf stock (${prod.current_stock} ${prod.unit})`, 'warning');
        return;
      }
      existing.quantity += 1;
    } else {
      this.cart.push({
        product_id: prod.id,
        name: prod.name,
        tamil_name: prod.tamil_name,
        unit: prod.unit,
        unit_price: prod.selling_price,
        gst_rate: prod.gst_rate || 5,
        max_stock: prod.current_stock,
        quantity: 1,
        discount: 0
      });
    }

    this.renderCart();
  },

  updateCartQty(prodId, delta) {
    const item = this.cart.find(it => it.product_id === prodId);
    if (!item) return;

    const newQty = item.quantity + delta;
    if (newQty <= 0) {
      this.cart = this.cart.filter(it => it.product_id !== prodId);
    } else if (newQty > item.max_stock) {
      showToast(`Cannot exceed shelf stock of ${item.max_stock} ${item.unit}`, 'warning');
      return;
    } else {
      item.quantity = newQty;
    }

    this.renderCart();
  },

  removeFromCart(prodId) {
    this.cart = this.cart.filter(it => it.product_id !== prodId);
    this.renderCart();
  },

  renderCart() {
    const listEl = document.getElementById('cart-items-list');
    const countEl = document.getElementById('cart-count');
    const checkoutBtn = document.getElementById('btn-checkout');

    if (!listEl) return;

    const totalItems = this.cart.reduce((acc, it) => acc + it.quantity, 0);
    countEl.innerText = `${totalItems} items`;

    if (this.cart.length === 0) {
      listEl.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); margin-top: 3.5rem; font-size: 0.85rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem; opacity: 0.5;">🛒</div>
          Scan barcode or click items to add to cart
        </div>
      `;
      document.getElementById('cart-subtotal').innerText = '₹0.00';
      document.getElementById('cart-cgst').innerText = '₹0.00';
      document.getElementById('cart-sgst').innerText = '₹0.00';
      document.getElementById('cart-total-gst').innerText = '₹0.00';
      document.getElementById('cart-grand-total').innerText = '₹0.00';
      checkoutBtn.disabled = true;
      return;
    }

    checkoutBtn.disabled = false;

    listEl.innerHTML = this.cart.map(it => `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <div class="cart-item-title">${it.name}</div>
          <div class="cart-item-subtitle">${formatINR(it.unit_price)} &bull; GST ${it.gst_rate}%</div>
        </div>
        <div class="cart-qty-controls">
          <button class="cart-qty-btn" onclick="POSView.updateCartQty(${it.product_id}, -1)">-</button>
          <span class="cart-qty-val">${it.quantity}</span>
          <button class="cart-qty-btn" onclick="POSView.updateCartQty(${it.product_id}, 1)">+</button>
        </div>
        <div class="cart-item-total">${formatINR(it.unit_price * it.quantity)}</div>
        <button class="cart-item-remove" onclick="POSView.removeFromCart(${it.product_id})">&times;</button>
      </div>
    `).join('');

    // Compute GST splits
    let subtotal = 0;
    let totalGST = 0;

    this.cart.forEach(it => {
      const lineTotal = it.unit_price * it.quantity;
      const baseValue = lineTotal / (1 + it.gst_rate / 100);
      const tax = lineTotal - baseValue;
      subtotal += baseValue;
      totalGST += tax;
    });

    const grandTotal = subtotal + totalGST;
    const cgst = totalGST / 2;
    const sgst = totalGST / 2;

    document.getElementById('cart-subtotal').innerText = formatINR(subtotal);
    document.getElementById('cart-cgst').innerText = formatINR(cgst);
    document.getElementById('cart-sgst').innerText = formatINR(sgst);
    document.getElementById('cart-total-gst').innerText = formatINR(totalGST);
    document.getElementById('cart-grand-total').innerText = formatINR(grandTotal);
  },

  async handleCheckout() {
    if (this.cart.length === 0) return;

    if (this.selectedPayment === 'UPI') {
      this.showUPIQRModal();
      return;
    }

    await this.completeTransaction();
  },

  showUPIQRModal() {
    let grandTotal = 0;
    this.cart.forEach(it => { grandTotal += it.unit_price * it.quantity; });

    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">📱 Scan UPI Dynamic QR Code</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 1.5rem; font-weight: 900; color: #059669; margin-bottom: 0.25rem;">
          ${formatINR(grandTotal)}
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.25rem;">
          Instant Zero-Fee Settlement via GPay, PhonePe, Paytm, or BHIM UPI
        </div>

        <div style="width: 180px; height: 180px; margin: 0 auto 1.25rem; background: #FFFFFF; padding: 10px; border: 2px solid #0F172A; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.06);">
          <svg viewBox="0 0 100 100" width="160" height="160">
            <rect width="100" height="100" fill="#FFFFFF"/>
            <!-- Corner Finder 1 -->
            <rect x="5" y="5" width="25" height="25" fill="#0F172A"/>
            <rect x="10" y="10" width="15" height="15" fill="#FFFFFF"/>
            <rect x="13" y="13" width="9" height="9" fill="#0F172A"/>
            <!-- Corner Finder 2 -->
            <rect x="70" y="5" width="25" height="25" fill="#0F172A"/>
            <rect x="75" y="10" width="15" height="15" fill="#FFFFFF"/>
            <rect x="78" y="13" width="9" height="9" fill="#0F172A"/>
            <!-- Corner Finder 3 -->
            <rect x="5" y="70" width="25" height="25" fill="#0F172A"/>
            <rect x="10" y="75" width="15" height="15" fill="#FFFFFF"/>
            <rect x="13" y="78" width="9" height="9" fill="#0F172A"/>
            <!-- Pattern dots -->
            <rect x="35" y="10" width="6" height="6" fill="#0F172A"/>
            <rect x="45" y="20" width="6" height="6" fill="#0F172A"/>
            <rect x="55" y="10" width="6" height="6" fill="#0F172A"/>
            <rect x="35" y="35" width="30" height="30" fill="#059669" rx="4"/>
            <text x="50" y="54" font-family="Outfit, sans-serif" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">UPI</text>
            <rect x="15" y="45" width="6" height="6" fill="#0F172A"/>
            <rect x="75" y="45" width="6" height="6" fill="#0F172A"/>
            <rect x="45" y="75" width="6" height="6" fill="#0F172A"/>
            <rect x="65" y="75" width="6" height="6" fill="#0F172A"/>
            <rect x="80" y="80" width="6" height="6" fill="#0F172A"/>
          </svg>
        </div>

        <p style="font-size: 0.775rem; color: #059669; font-weight: 700;">
          UPI ID: srimurugan@okaxis &bull; Sri Murugan Super Store
        </p>

        <div style="display: flex; justify-content: center; gap: 0.75rem; margin-top: 1.5rem;">
          <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button class="btn btn-ai" id="btn-upi-paid">
            <span>✓</span> Confirm Payment Received
          </button>
        </div>
      </div>
    `;

    App.openModal();
    document.getElementById('btn-upi-paid').addEventListener('click', async () => {
      App.closeModal();
      await POSView.completeTransaction();
    });
  },

  async completeTransaction() {
    const custName = document.getElementById('cust-name-input')?.value.trim() || 'Walk-in Customer';
    const custPhone = document.getElementById('cust-phone-input')?.value.trim() || '';

    const payload = {
      customer_name: custName,
      customer_phone: custPhone,
      payment_method: this.selectedPayment,
      items: this.cart.map(it => ({
        product_id: it.product_id,
        quantity: it.quantity,
        unit_price: it.unit_price,
        discount: it.discount || 0
      }))
    };

    try {
      const res = await API.post('/api/pos/checkout', payload);
      showToast(`Sale completed! Invoice #${res.invoice_number} created.`, 'success');
      this.showReceiptModal(res);
      this.cart = [];
      this.renderCart();
      await this.loadInitialData();
    } catch (e) {
      console.error('Checkout failed', e);
    }
  },

  showReceiptModal(sale) {
    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">🖨️ Retail Thermal Receipt</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div class="thermal-receipt" id="printable-receipt">
        <div class="receipt-header">
          <div class="receipt-title">SRI MURUGAN SUPER STORE</div>
          <div>42, Usman Road, T. Nagar, Chennai - 600017</div>
          <div>GSTIN: 33AAAAA0000A1Z5 | Ph: +91 98400 12345</div>
          <div class="receipt-divider"></div>
          <div class="receipt-line">
            <span>Invoice: <b>${sale.invoice_number}</b></span>
            <span>Date: ${new Date().toLocaleDateString('en-IN')}</span>
          </div>
          <div class="receipt-line">
            <span>Customer: ${sale.customer_name}</span>
            <span>Pay: ${sale.payment_method}</span>
          </div>
        </div>

        <div style="margin: 0.5rem 0;">
          ${(sale.items || []).map(it => `
            <div class="receipt-line">
              <span>${it.product_name || 'Item'} &times; ${it.quantity}</span>
              <span>${formatINR(it.total_price)}</span>
            </div>
          `).join('')}
        </div>

        <div class="receipt-divider"></div>
        <div class="receipt-line"><span>Subtotal (Base):</span><span>${formatINR(sale.subtotal)}</span></div>
        <div class="receipt-line"><span>CGST:</span><span>${formatINR(sale.cgst_amount || sale.gst_amount / 2)}</span></div>
        <div class="receipt-line"><span>SGST (TN):</span><span>${formatINR(sale.sgst_amount || sale.gst_amount / 2)}</span></div>
        <div class="receipt-divider"></div>
        <div class="receipt-line" style="font-size: 0.95rem; font-weight: bold;">
          <span>GRAND TOTAL:</span>
          <span>${formatINR(sale.total_amount)}</span>
        </div>
        <div class="receipt-divider"></div>
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.725rem; color: #4B5563;">
          நன்றி, மீண்டும் வருக! (Thank You, Visit Again!)<br/>
          Software: Inventory AI Retail
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="App.closeModal()">Close</button>
        <button class="btn btn-primary" onclick="window.print()">Print Receipt</button>
      </div>
    `;

    App.openModal();
  }
};
