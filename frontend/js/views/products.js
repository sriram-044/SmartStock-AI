// ==============================================================================
// Inventory Management AI: Product Catalog View Controller
// ==============================================================================

const ProductsView = {
  products: [],
  categories: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Retail Product Catalog</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Manage SKUs, bilingual names, units, GST tax slabs, and inventory safety parameters
          </p>
        </div>
        <button class="btn btn-primary" id="btn-add-product">
          <span>➕</span> Add New Product
        </button>
      </div>

      <!-- Filter Controls Bar -->
      <div class="glass-card" style="padding: 1rem; margin-bottom: 1.25rem; display: flex; gap: 1rem; align-items: center;">
        <div class="search-input-wrap" style="flex: 2;">
          <span class="icon">🔍</span>
          <input type="text" id="prod-filter-search" class="form-control" placeholder="Search by name, Tamil name, barcode..." />
        </div>
        <div style="flex: 1;">
          <select id="prod-filter-category" class="form-control">
            <option value="">All Categories</option>
          </select>
        </div>
        <div style="flex: 1;">
          <select id="prod-filter-status" class="form-control">
            <option value="">All Stock Statuses</option>
            <option value="CRITICAL">Critical Stock</option>
            <option value="LOW">Reorder Soon</option>
            <option value="SAFE">Safe Stock</option>
            <option value="OVERSTOCK">Overstocked</option>
          </select>
        </div>
      </div>

      <!-- Products Data Table -->
      <div class="glass-card" style="padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product Name</th>
                <th>Category</th>
                <th>Unit / Pack</th>
                <th>Purchase (₹)</th>
                <th>Selling / MRP</th>
                <th>GST Rate</th>
                <th>Current Stock</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="products-table-body">
              <tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Loading products...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    document.getElementById('btn-add-product').addEventListener('click', () => {
      this.showProductModal();
    });

    const searchInput = document.getElementById('prod-filter-search');
    let timer = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => this.loadProducts(), 250);
    });

    document.getElementById('prod-filter-category').addEventListener('change', () => this.loadProducts());
    document.getElementById('prod-filter-status').addEventListener('change', () => this.loadProducts());

    await this.loadInitial();
  },

  async loadInitial() {
    try {
      this.categories = await API.get('/api/products/categories');
      const catSelect = document.getElementById('prod-filter-category');
      if (catSelect) {
        catSelect.innerHTML = '<option value="">All Categories</option>' +
          this.categories.map(c => `<option value="${c.id}">${c.name} (${c.tamil_name || ''})</option>`).join('');
      }
      await this.loadProducts();
    } catch (e) {
      console.error('Failed loading initial products', e);
    }
  },

  async loadProducts() {
    const search = document.getElementById('prod-filter-search')?.value || '';
    const catId = document.getElementById('prod-filter-category')?.value || '';
    const status = document.getElementById('prod-filter-status')?.value || '';

    try {
      const res = await API.get('/api/products', {
        search,
        category_id: catId,
        stock_status: status,
        limit: 100
      });
      this.products = res.items || [];
      this.renderTable();
    } catch (e) {
      console.error('Failed loading products list', e);
    }
  },

  renderTable() {
    const tbody = document.getElementById('products-table-body');
    if (!tbody) return;

    if (this.products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 2rem;">No products match criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.products.map(p => `
      <tr>
        <td>
          <div style="font-weight: 700; color: var(--text-primary);">${p.name}</div>
          <div style="font-size: 0.75rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">Barcode: ${p.barcode || 'N/A'}</div>
        </td>
        <td>${p.category_name || '-'}</td>
        <td>${p.unit} <span style="font-size: 0.725rem; color: var(--text-muted);">${p.pack_size ? `(${p.pack_size})` : ''}</span></td>
        <td>${formatINR(p.purchase_price)}</td>
        <td>
          <div>${formatINR(p.selling_price)}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">MRP: ${formatINR(p.mrp)}</div>
        </td>
        <td>
          <span class="status-badge" style="background: rgba(255,255,255,0.06); color: var(--text-primary); border: 1px solid var(--border-color);">
            ${p.gst_rate}%
          </span>
        </td>
        <td>
          <div style="font-weight: 700; font-size: 0.95rem;">${p.current_stock}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">Min: ${p.min_stock} | Reorder: ${p.reorder_level}</div>
        </td>
        <td>
          <span class="status-badge badge-${p.stock_status === 'SAFE' ? 'safe' : p.stock_status === 'CRITICAL' ? 'critical' : p.stock_status === 'LOW' ? 'monitor' : 'warning'}">
            <span class="badge-dot"></span> ${p.stock_status_label}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="ProductsView.showProductModal(${p.id})">
            Edit
          </button>
        </td>
      </tr>
    `).join('');
  },

  showProductModal(productId = null) {
    const isEdit = productId !== null;
    const prod = isEdit ? this.products.find(p => p.id === productId) : null;
    const modal = document.getElementById('app-modal');

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">${isEdit ? 'Edit Product' : 'Add New Retail Product'}</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <form id="product-form">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label class="form-label">Product Name (English) *</label>
            <input type="text" id="m-name" class="form-control" value="${prod?.name || ''}" required />
          </div>
          <div class="form-group">
            <label class="form-label">Tamil Name (தமிழ் பெயர்)</label>
            <input type="text" id="m-tamil-name" class="form-control" value="${prod?.tamil_name || ''}" />
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label class="form-label">Barcode / SKU</label>
            <input type="text" id="m-barcode" class="form-control" value="${prod?.barcode || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label">Category *</label>
            <select id="m-category" class="form-control" required>
              ${this.categories.map(c => `<option value="${c.id}" ${prod?.category_id == c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label class="form-label">Unit *</label>
            <select id="m-unit" class="form-control">
              ${['Piece', 'Kg', 'Gram', 'Litre', 'Millilitre', 'Pack', 'Box', 'Bottle', 'Dozen'].map(u => `
                <option value="${u}" ${prod?.unit === u ? 'selected' : ''}>${u}</option>
              `).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Purchase Price (₹) *</label>
            <input type="number" step="0.01" id="m-purchase-price" class="form-control" value="${prod?.purchase_price || ''}" required />
          </div>
          <div class="form-group">
            <label class="form-label">Selling Price (₹) *</label>
            <input type="number" step="0.01" id="m-selling-price" class="form-control" value="${prod?.selling_price || ''}" required />
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label class="form-label">MRP (₹)</label>
            <input type="number" step="0.01" id="m-mrp" class="form-control" value="${prod?.mrp || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label">GST Tax Rate *</label>
            <select id="m-gst" class="form-control">
              ${[0, 5, 12, 18, 28].map(g => `<option value="${g}" ${prod?.gst_rate == g ? 'selected' : ''}>${g}%</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Reorder Level *</label>
            <input type="number" id="m-reorder-level" class="form-control" value="${prod?.reorder_level || 20}" required />
          </div>
        </div>

        ${!isEdit ? `
          <div class="form-group">
            <label class="form-label">Initial Opening Stock</label>
            <input type="number" id="m-opening-stock" class="form-control" value="20" />
          </div>
        ` : ''}

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">${isEdit ? 'Update Product' : 'Create Product'}</button>
        </div>
      </form>
    `;

    App.openModal();

    document.getElementById('product-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('m-name').value.trim(),
        tamil_name: document.getElementById('m-tamil-name').value.trim() || null,
        barcode: document.getElementById('m-barcode').value.trim() || null,
        category_id: parseInt(document.getElementById('m-category').value),
        unit: document.getElementById('m-unit').value,
        purchase_price: parseFloat(document.getElementById('m-purchase-price').value),
        selling_price: parseFloat(document.getElementById('m-selling-price').value),
        mrp: parseFloat(document.getElementById('m-mrp').value || document.getElementById('m-selling-price').value),
        gst_rate: parseFloat(document.getElementById('m-gst').value),
        reorder_level: parseInt(document.getElementById('m-reorder-level').value),
        min_stock: Math.floor(parseInt(document.getElementById('m-reorder-level').value) / 2),
        max_stock: parseInt(document.getElementById('m-reorder-level').value) * 4
      };

      if (!isEdit) {
        payload.opening_stock = parseFloat(document.getElementById('m-opening-stock').value || 0);
      }

      try {
        if (isEdit) {
          await API.put(`/api/products/${productId}`, payload);
          showToast('Product updated successfully!', 'success');
        } else {
          await API.post('/api/products', payload);
          showToast('Product created successfully!', 'success');
        }
        App.closeModal();
        await ProductsView.loadProducts();
      } catch (err) {
        console.error('Save product error', err);
      }
    });
  }
};
