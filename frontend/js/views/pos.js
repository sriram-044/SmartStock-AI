// ==============================================================================
// Inventory Management AI: POS Billing Terminal & Thermal Receipt Controller
// ==============================================================================

const POSView = {
  cart: [],
  selectedPayment: 'CASH',
  products: [],

  async render(container) {
    this.cart = [];
    this.selectedPayment = 'CASH';

    container.innerHTML = `
      <div class="pos-container">
        <!-- Left Panel: Product Catalog & Search -->
        <div class="pos-catalog-panel">
          <div class="pos-search-bar">
            <div class="search-input-wrap" style="flex: 1;">
              <span class="icon">🔍</span>
              <input type="text" id="pos-search-input" class="form-control" placeholder="Search by name, Tamil name, or scan barcode..." autofocus />
            </div>
            <div class="barcode-badge-indicator">
              <span>⚡ BARCODE READY</span>
            </div>
          </div>

          <div class="pos-category-chips" id="pos-category-chips">
            <div class="cat-chip active" data-cat="">All Items</div>
          </div>

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

          <div class="cart-items-list" id="cart-items-list">
            <div style="text-align: center; color: var(--text-muted); margin-top: 3rem; font-size: 0.85rem;">
              <div style="font-size: 2.5rem; margin-bottom: 0.5rem; opacity: 0.4;">🛒</div>
              Scan barcode or click items to add to cart
            </div>
          </div>

          <!-- Customer details collapsible -->
          <div style="padding: 0.5rem 1.25rem; border-top: 1px solid var(--border-color); display: flex; gap: 0.5rem;">
            <input type="text" id="cust-name-input" class="form-control" style="font-size: 0.775rem; padding: 0.4rem 0.6rem;" placeholder="Customer Name (Default: Walk-in)" />
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
              <span id="cart-total-gst" style="color: var(--accent-saffron);">₹0.00</span>
            </div>
            <div class="summary-line total-line">
              <span>Grand Total:</span>
              <span id="cart-grand-total" style="color: var(--brand-primary);">₹0.00</span>
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
              <span style="font-size: 1.1rem;">💳</span> Debit Card
            </button>
            <button class="pay-btn" data-method="CREDIT">
              <span style="font-size: 1.1rem;">📝</span> Khata / Credit
            </button>
          </div>

          <button id="btn-checkout" class="btn btn-primary cart-checkout-btn" disabled>
            <span>Proceed to Bill & Print Receipt</span>
          </button>
        </div>
      </div>
    `;

    this.bindEvents();
    await this.loadCatalog();
  },

  async loadCatalog(search = '', categoryId = '') {
    try {
      const [prodsRes, cats] = await Promise.all([
        API.get('/api/products', { search, category_id: categoryId, limit: 100 }),
        API.get('/api/products/categories')
      ]);

      this.products = prodsRes.items || [];
      this.renderCategoryChips(cats, categoryId);
      this.renderProductGrid();
    } catch (e) {
      console.error('Failed loading POS catalog', e);
    }
  },

  renderCategoryChips(categories, activeCatId) {
    const chipContainer = document.getElementById('pos-category-chips');
    if (!chipContainer) return;
    chipContainer.innerHTML = `
      <div class="cat-chip ${!activeCatId ? 'active' : ''}" data-cat="">All Items</div>
      ${categories.map(c => `
        <div class="cat-chip ${activeCatId == c.id ? 'active' : ''}" data-cat="${c.id}">
          ${c.name}
        </div>
      `).join('')}
    `;

    chipContainer.querySelectorAll('.cat-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const catId = chip.getAttribute('data-cat');
        this.loadCatalog(document.getElementById('pos-search-input').value, catId);
      });
    });
  },

  renderProductGrid() {
    const grid = document.getElementById('pos-product-grid');
    if (!grid) return;

    if (this.products.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">No matching products in catalog.</div>`;
      return;
    }

    grid.innerHTML = this.products.map(p => {
      const isOutOfStock = p.current_stock <= 0;
      return `
        <div class="pos-item-card ${isOutOfStock ? 'out-of-stock' : ''}" 
             style="${isOutOfStock ? 'opacity: 0.5; pointer-events: none;' : ''}"
             onclick="POSView.addToCart(${p.id})">
          <div class="pos-item-header">
            <span class="pos-item-name">${p.name}</span>
            <span class="pos-item-tamil">${p.tamil_name || ''}</span>
            <span class="pos-item-stock">Stock: ${p.current_stock} ${p.unit}</span>
          </div>
          <div class="pos-item-footer">
            <span class="pos-item-price">${formatINR(p.selling_price)}</span>
            <span class="status-badge badge-${p.stock_status === 'SAFE' ? 'safe' : p.stock_status === 'CRITICAL' ? 'critical' : 'warning'}" style="padding: 0.15rem 0.4rem; font-size: 0.65rem;">
              GST ${p.gst_rate}%
            </span>
          </div>
        </div>
      `;
    }).join('');
  },

  addToCart(productId) {
    const prod = this.products.find(p => p.id === productId);
    if (!prod) return;

    const existing = this.cart.find(item => item.product_id === productId);
    if (existing) {
      if (existing.quantity + 1 > prod.current_stock) {
        showToast(`Stock limit reached for '${prod.name}' (${prod.current_stock} available)`, 'error');
        return;
      }
      existing.quantity += 1;
    } else {
      if (prod.current_stock < 1) {
        showToast(`'${prod.name}' is out of stock!`, 'error');
        return;
      }
      this.cart.push({
        product_id: productId,
        product: prod,
        quantity: 1,
        discount: 0.0
      });
    }

    this.renderCart();
  },

  updateQty(productId, delta) {
    const item = this.cart.find(i => i.product_id === productId);
    if (!item) return;
    const newQty = item.quantity + delta;
    if (newQty <= 0) {
      this.cart = this.cart.filter(i => i.product_id !== productId);
    } else {
      if (newQty > item.product.current_stock) {
        showToast(`Cannot exceed current stock (${item.product.current_stock} ${item.product.unit})`, 'error');
        return;
      }
      item.quantity = newQty;
    }
    this.renderCart();
  },

  removeFromCart(productId) {
    this.cart = this.cart.filter(i => i.product_id !== productId);
    this.renderCart();
  },

  renderCart() {
    const list = document.getElementById('cart-items-list');
    const countEl = document.getElementById('cart-count');
    const checkoutBtn = document.getElementById('btn-checkout');

    if (!list) return;

    countEl.innerText = `${this.cart.length} item${this.cart.length !== 1 ? 's' : ''}`;
    checkoutBtn.disabled = this.cart.length === 0;

    if (this.cart.length === 0) {
      list.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); margin-top: 3rem; font-size: 0.85rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem; opacity: 0.4;">🛒</div>
          Scan barcode or click items to add to cart
        </div>
      `;
      this.updateTotals(0, 0, 0);
      return;
    }

    let subtotal = 0;
    let totalGst = 0;
    let grandTotal = 0;

    list.innerHTML = this.cart.map(item => {
      const p = item.product;
      const price = p.selling_price;
      const basePrice = price / (1.0 + (p.gst_rate / 100.0));
      const lineGst = (price - basePrice) * item.quantity;
      const lineTotal = price * item.quantity;

      subtotal += basePrice * item.quantity;
      totalGst += lineGst;
      grandTotal += lineTotal;

      return `
        <div class="cart-item-row">
          <div class="cart-item-info">
            <div class="cart-item-name">${p.name}</div>
            <div class="cart-item-sub">₹${price} / ${p.unit} (GST ${p.gst_rate}%)</div>
          </div>
          <div class="qty-control">
            <div class="qty-btn" onclick="POSView.updateQty(${p.id}, -1)">-</div>
            <span class="qty-display">${item.quantity}</span>
            <div class="qty-btn" onclick="POSView.updateQty(${p.id}, 1)">+</div>
          </div>
          <div class="cart-item-total">${formatINR(lineTotal)}</div>
          <div class="cart-item-remove" onclick="POSView.removeFromCart(${p.id})">✕</div>
        </div>
      `;
    }).join('');

    this.updateTotals(subtotal, totalGst, grandTotal);
  },

  updateTotals(subtotal, gst, grandTotal) {
    document.getElementById('cart-subtotal').innerText = formatINR(subtotal);
    document.getElementById('cart-cgst').innerText = formatINR(gst / 2);
    document.getElementById('cart-sgst').innerText = formatINR(gst / 2);
    document.getElementById('cart-total-gst').innerText = formatINR(gst);
    document.getElementById('cart-grand-total').innerText = formatINR(grandTotal);
  },

  bindEvents() {
    // Search input
    const searchInput = document.getElementById('pos-search-input');
    let timer = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const val = e.target.value.trim();
        // Check if scanned exact barcode
        if (/^\d{8,14}$/.test(val)) {
          try {
            const p = await API.get(`/api/products/barcode/${val}`);
            if (p) {
              POSView.addToCart(p.id);
              searchInput.value = '';
              showToast(`Scanned: ${p.name}`, 'success');
              return;
            }
          } catch (err) {}
        }
        POSView.loadCatalog(val);
      }, 250);
    });

    // Clear cart
    document.getElementById('btn-clear-cart').addEventListener('click', () => {
      POSView.cart = [];
      POSView.renderCart();
    });

    // Payment methods toggle
    document.querySelectorAll('.pay-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.pay-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        POSView.selectedPayment = btn.getAttribute('data-method');
      });
    });

    // Checkout button
    document.getElementById('btn-checkout').addEventListener('click', () => {
      POSView.handleCheckout();
    });
  },

  async handleCheckout() {
    if (this.cart.length === 0) return;

    const custName = document.getElementById('cust-name-input').value.trim() || 'Walk-in Customer';
    const custPhone = document.getElementById('cust-phone-input').value.trim() || null;

    // If UPI selected, show simulated UPI payment QR modal
    if (this.selectedPayment === 'UPI') {
      this.showUPIModal(async () => {
        await this.executeSaleCheckout(custName, custPhone);
      });
    } else {
      await this.executeSaleCheckout(custName, custPhone);
    }
  },

  showUPIModal(onSuccess) {
    const modal = document.getElementById('app-modal');
    const grandTotal = document.getElementById('cart-grand-total').innerText;
    
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">📱 Scan UPI QR Code to Pay</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="text-align: center; padding: 1.5rem;">
        <div style="width: 180px; height: 180px; margin: 0 auto 1.25rem; background: #FFFFFF; padding: 10px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
          <!-- Dynamic QR SVG Simulation -->
          <svg viewBox="0 0 100 100" width="100%" height="100%">
            <rect width="100" height="100" fill="#fff" />
            <rect x="10" y="10" width="25" height="25" fill="#000" />
            <rect x="65" y="10" width="25" height="25" fill="#000" />
            <rect x="10" y="65" width="25" height="25" fill="#000" />
            <rect x="15" y="15" width="15" height="15" fill="#fff" />
            <rect x="70" y="15" width="15" height="15" fill="#fff" />
            <rect x="15" y="70" width="15" height="15" fill="#fff" />
            <rect x="18" y="18" width="9" height="9" fill="#000" />
            <rect x="73" y="18" width="9" height="9" fill="#000" />
            <rect x="18" y="73" width="9" height="9" fill="#000" />
            <rect x="42" y="15" width="16" height="16" fill="#10B981" />
            <rect x="42" y="65" width="16" height="16" fill="#06B6D4" />
            <rect x="65" y="42" width="16" height="16" fill="#F59E0B" />
          </svg>
        </div>
        <div style="font-size: 1.25rem; font-weight: 800; color: var(--brand-primary); margin-bottom: 0.25rem;">
          ${grandTotal}
        </div>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
          UPI ID: <strong>srimurugan.store@upi</strong> (GPay / PhonePe / Paytm)
        </p>
        <button class="btn btn-primary" style="width: 100%;" id="btn-upi-confirm">
          Simulate Successful Payment Received (₹)
        </button>
      </div>
    `;

    App.openModal();
    document.getElementById('btn-upi-confirm').addEventListener('click', () => {
      App.closeModal();
      onSuccess();
    });
  },

  async executeSaleCheckout(custName, custPhone) {
    const checkoutBtn = document.getElementById('btn-checkout');
    checkoutBtn.disabled = true;
    checkoutBtn.innerText = 'Processing Bill...';

    try {
      const payload = {
        items: this.cart.map(i => ({
          product_id: i.product_id,
          quantity: i.quantity,
          discount: i.discount || 0
        })),
        payment_method: this.selectedPayment,
        customer_name: custName,
        customer_phone: custPhone
      };

      const invoice = await API.post('/api/pos/checkout', payload);
      showToast(`Sale Invoice #${invoice.invoice_number} created! Stock decremented.`, 'success');
      
      this.cart = [];
      this.renderCart();
      await this.loadCatalog(); // Refresh remaining stock counts
      this.showReceiptModal(invoice);
    } catch (err) {
      console.error('Checkout failed', err);
    } finally {
      checkoutBtn.disabled = false;
      checkoutBtn.innerText = 'Proceed to Bill & Print Receipt';
    }
  },

  showReceiptModal(invoice) {
    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">🧾 Tax Invoice Receipt</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div class="thermal-receipt" id="printable-receipt">
        <div class="receipt-header">
          <div class="receipt-shop-name">SRI MURUGAN SUPER STORE</div>
          <div class="receipt-tamil-shop-name">ஸ்ரீ முருகன் சூப்பர் ஸ்டோர்</div>
          <div>124, Usman Road, T. Nagar, Chennai - 600017</div>
          <div>GSTIN: 33AAAAA0000A1Z5 | Ph: +91 98400 12345</div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.775rem;">
          <span>Invoice: <b>${invoice.invoice_number}</b></span>
          <span>${invoice.created_at ? invoice.created_at.substring(0, 16) : ''}</span>
        </div>
        <div style="font-size: 0.775rem; margin-bottom: 0.5rem;">
          <span>Customer: ${invoice.customer_name}</span>
          ${invoice.customer_phone ? ` | ${invoice.customer_phone}` : ''}
        </div>

        <table class="receipt-table">
          <thead>
            <tr style="border-bottom: 1px solid #000; border-top: 1px solid #000;">
              <th>Item</th>
              <th style="text-align: center;">Qty</th>
              <th style="text-align: right;">Rate</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            ${(invoice.items || []).map(it => `
              <tr>
                <td>${it.product_name}</td>
                <td style="text-align: center;">${it.quantity}</td>
                <td style="text-align: right;">${it.unit_price.toFixed(2)}</td>
                <td>${it.total.toFixed(2)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="receipt-dashed">
          <div style="display: flex; justify-content: space-between;">
            <span>Subtotal (Base):</span>
            <span>₹${invoice.subtotal.toFixed(2)}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span>CGST (Central Tax):</span>
            <span>₹${(invoice.gst_amount / 2).toFixed(2)}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span>SGST (State Tax):</span>
            <span>₹${(invoice.gst_amount / 2).toFixed(2)}</span>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: bold; margin: 0.5rem 0;">
          <span>GRAND TOTAL:</span>
          <span>₹${invoice.total_amount.toFixed(2)}</span>
        </div>

        <div style="font-size: 0.75rem; text-align: center; margin-top: 0.85rem;">
          <div>Paid via: <b>${invoice.payment_method}</b></div>
          <div style="margin-top: 0.35rem;">நன்றி! மீண்டும் வருக! (Thank You! Visit Again!)</div>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem;">
        <button class="btn btn-secondary" onclick="App.closeModal()">Close</button>
        <button class="btn btn-primary" onclick="window.print()">
          <span>🖨️</span> Print Thermal Invoice
        </button>
      </div>
    `;

    App.openModal();
  }
};
