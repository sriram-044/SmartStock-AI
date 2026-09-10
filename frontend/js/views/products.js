// ==============================================================================
// Inventory Management AI: Product Catalog View Controller (Cards & Table Toggle)
// ==============================================================================

const ProductsView = {
  products: [],
  categories: [],
  viewMode: 'cards', // 'cards' or 'table'

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem; font-weight: 900; color: var(--text-primary);">Retail Product Catalog</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Manage SKUs, bilingual names, GST tax slabs, barcodes, and inventory safety parameters
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <!-- Grid / Table Toggle Switch -->
          <div class="glass-card-subtle" style="padding: 0.25rem 0.35rem; display: flex; gap: 0.25rem;">
            <button class="btn btn-sm ${this.viewMode === 'cards' ? 'btn-primary' : 'btn-secondary'}" id="btn-view-cards" style="border: none;">
              🔲 Cards
            </button>
            <button class="btn btn-sm ${this.viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}" id="btn-view-table" style="border: none;">
              📑 Table
            </button>
          </div>
          <button class="btn btn-primary" id="btn-add-product">
            <span>➕</span> Add Product
          </button>
        </div>
      </div>

      <!-- Filter Controls Bar -->
      <div class="glass-card" style="padding: 0.85rem 1.25rem; margin-bottom: 1.5rem; display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
        <div class="search-input-wrap" style="flex: 2; min-width: 220px;">
          <span class="icon">🔍</span>
          <input type="text" id="prod-filter-search" class="form-control" placeholder="Search product name, Tamil name, barcode..." />
        </div>
        <div style="flex: 1; min-width: 160px;">
          <select id="prod-filter-category" class="form-control">
            <option value="">All Categories</option>
          </select>
        </div>
        <div style="flex: 1; min-width: 160px;">
          <select id="prod-filter-status" class="form-control">
            <option value="">All Stock Statuses</option>
            <option value="CRITICAL">Critical Stock</option>
            <option value="LOW">Reorder Soon</option>
            <option value="SAFE">Safe Stock</option>
            <option value="OVERSTOCK">Overstocked</option>
          </select>
        </div>
      </div>

      <!-- Products Display Container -->
      <div id="products-content-container">
        <p style="color: var(--text-muted); font-size: 0.85rem;">Loading products...</p>
      </div>
    `;

    document.getElementById('btn-add-product').addEventListener('click', () => {
      this.showProductModal();
    });

    document.getElementById('btn-view-cards').addEventListener('click', () => {
      this.viewMode = 'cards';
      this.renderViewToggle();
      this.renderProducts();
    });

    document.getElementById('btn-view-table').addEventListener('click', () => {
      this.viewMode = 'table';
      this.renderViewToggle();
      this.renderProducts();
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

  renderViewToggle() {
    const cardsBtn = document.getElementById('btn-view-cards');
    const tableBtn = document.getElementById('btn-view-table');
    if (!cardsBtn || !tableBtn) return;

    if (this.viewMode === 'cards') {
      cardsBtn.className = 'btn btn-sm btn-primary';
      tableBtn.className = 'btn btn-sm btn-secondary';
    } else {
      cardsBtn.className = 'btn btn-sm btn-secondary';
      tableBtn.className = 'btn btn-sm btn-primary';
    }
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
    const query = document.getElementById('prod-filter-search')?.value.trim() || '';
    const categoryId = document.getElementById('prod-filter-category')?.value || '';
    const status = document.getElementById('prod-filter-status')?.value || '';

    try {
      const res = await API.get('/api/products', {
        search: query,
        category_id: categoryId,
        status: status,
        limit: 150
      });
      this.products = res.items || [];
      this.renderProducts();
    } catch (e) {
      console.error('Failed loading products', e);
    }
  },

  renderProducts() {
    const container = document.getElementById('products-content-container');
    if (!container) return;

    if (this.products.length === 0) {
      container.innerHTML = `
        <div class="glass-card" style="text-align: center; padding: 3.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📦</div>
          <h3 style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.25rem;">No Products Found</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.25rem;">
            Try adjusting your search filters or add a new product SKU.
          </p>
          <button class="btn btn-primary btn-sm" onclick="ProductsView.showProductModal()">
            ➕ Add Product
          </button>
        </div>
      `;
      return;
    }

    if (this.viewMode === 'cards') {
      // Modern Product Cards View
      container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.25rem;">
          ${this.products.map(p => {
            const stockPct = Math.min(100, Math.round((p.current_stock / (p.reorder_point * 2 || 30)) * 100));
            const statusClass = p.status === 'CRITICAL' ? 'badge-critical' : (p.status === 'LOW' ? 'badge-warning' : 'badge-safe');

            return `
              <div class="glass-card" style="display: flex; flex-direction: column; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                  <span class="status-badge ${statusClass}" style="font-size: 0.68rem;">
                    <span class="badge-dot"></span> ${p.status || 'IN STOCK'}
                  </span>
                  <span style="font-size: 0.7rem; color: var(--text-muted); font-family: var(--font-mono);">
                    ${p.barcode || 'NO BARCODE'}
                  </span>
                </div>

                <div style="height: 85px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem;">
                  ${Assets.getProductImage(p.name, p.category_name || '')}
                </div>

                <div style="font-weight: 800; font-size: 0.95rem; color: var(--text-primary); line-height: 1.25; margin-bottom: 0.15rem;">
                  ${p.name}
                </div>
                <div style="font-size: 0.75rem; color: var(--brand-primary); font-weight: 600; margin-bottom: 0.5rem;">
                  ${p.tamil_name || ''}
                </div>

                <div style="margin-bottom: 0.75rem;">
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.25rem;">
                    <span>Stock: ${p.current_stock} ${p.unit}</span>
                    <span style="color: var(--text-muted);">Reorder: ${p.reorder_point} ${p.unit}</span>
                  </div>
                  <div style="height: 6px; background: #F3F4F6; border-radius: 9999px; overflow: hidden;">
                    <div style="height: 100%; width: ${stockPct}%; background: ${p.current_stock <= p.reorder_point ? '#EF4444' : '#22C55E'};"></div>
                  </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: auto; padding-top: 0.75rem; border-top: 1px dashed var(--border-color); margin-bottom: 0.75rem;">
                  <div>
                    <span style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase;">Cost:</span>
                    <strong style="font-size: 0.85rem; color: var(--text-secondary);">${formatINR(p.purchase_price)}</strong>
                  </div>
                  <div>
                    <span style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase;">MRP / Sell:</span>
                    <strong style="font-size: 1.15rem; color: var(--text-primary); font-family: var(--font-heading);">${formatINR(p.selling_price)}</strong>
                  </div>
                </div>

                <div style="display: flex; gap: 0.4rem;">
                  <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="ProductsView.showProductModal(${p.id})">
                    ✏️ Edit
                  </button>
                  <button class="btn btn-primary btn-sm" style="flex: 1;" onclick="App.navigate('ai-recom')">
                    ⚡ Restock
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      // Table View
      container.innerHTML = `
        <div class="glass-card" style="padding: 0;">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Unit</th>
                  <th>Purchase (₹)</th>
                  <th>Selling / MRP</th>
                  <th>GST Rate</th>
                  <th>Current Stock</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${this.products.map(p => `
                  <tr>
                    <td>
                      <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="width: 36px; height: 36px; flex-shrink: 0;">
                          ${Assets.getProductImage(p.name, p.category_name || '')}
                        </div>
                        <div>
                          <div style="font-weight: 700;">${p.name}</div>
                          <div style="font-size: 0.725rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
                        </div>
                      </div>
                    </td>
                    <td>${p.category_name || '-'}</td>
                    <td>${p.unit}</td>
                    <td>${formatINR(p.purchase_price)}</td>
                    <td style="font-weight: 700;">${formatINR(p.selling_price)}</td>
                    <td><span class="status-badge badge-monitor" style="font-size: 0.68rem;">${p.gst_rate}%</span></td>
                    <td style="font-weight: 800;">${p.current_stock} ${p.unit}</td>
                    <td>
                      <span class="status-badge ${p.status === 'CRITICAL' ? 'badge-critical' : (p.status === 'LOW' ? 'badge-warning' : 'badge-safe')}">
                        ${p.status || 'IN STOCK'}
                      </span>
                    </td>
                    <td>
                      <button class="btn btn-secondary btn-sm" onclick="ProductsView.showProductModal(${p.id})">
                        Edit
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }
  },

  async showProductModal(productId = null) {
    let prod = {
      name: '',
      tamil_name: '',
      category_id: 1,
      barcode: '',
      unit: 'pack',
      purchase_price: '',
      selling_price: '',
      gst_rate: 5,
      current_stock: 0,
      safety_stock: 10,
      reorder_point: 15
    };

    if (productId) {
      try {
        prod = await API.get(`/api/products/${productId}`);
      } catch (e) {}
    }

    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">${productId ? '✏️ Edit Product SKU' : '➕ Add New Product'}</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <form id="prod-modal-form" style="display: flex; flex-direction: column; gap: 0.85rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem;">
          <div class="form-group">
            <label class="form-label">Product Name (English) *</label>
            <input type="text" id="m-prod-name" class="form-control" value="${prod.name || ''}" placeholder="e.g. Ponni Boiled Rice 25kg" required />
          </div>
          <div class="form-group">
            <label class="form-label">Tamil Name (தமிழ்) *</label>
            <input type="text" id="m-prod-tamil" class="form-control" value="${prod.tamil_name || ''}" placeholder="e.g. பொன்னி புழுங்கல் அரிசி" />
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.85rem;">
          <div class="form-group">
            <label class="form-label">Category *</label>
            <select id="m-prod-cat" class="form-control">
              ${this.categories.map(c => `<option value="${c.id}" ${c.id === prod.category_id ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Barcode / SKU</label>
            <input type="text" id="m-prod-barcode" class="form-control" value="${prod.barcode || ''}" placeholder="8901030..." />
          </div>
          <div class="form-group">
            <label class="form-label">Unit of Measure *</label>
            <select id="m-prod-unit" class="form-control">
              <option value="pack" ${prod.unit === 'pack' ? 'selected' : ''}>pack</option>
              <option value="kg" ${prod.unit === 'kg' ? 'selected' : ''}>kg</option>
              <option value="litre" ${prod.unit === 'litre' ? 'selected' : ''}>litre</option>
              <option value="bottle" ${prod.unit === 'bottle' ? 'selected' : ''}>bottle</option>
              <option value="bag" ${prod.unit === 'bag' ? 'selected' : ''}>bag</option>
              <option value="box" ${prod.unit === 'box' ? 'selected' : ''}>box</option>
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.85rem;">
          <div class="form-group">
            <label class="form-label">Purchase Cost (₹) *</label>
            <input type="number" step="0.01" id="m-prod-buy" class="form-control" value="${prod.purchase_price || ''}" required />
          </div>
          <div class="form-group">
            <label class="form-label">Selling MRP (₹) *</label>
            <input type="number" step="0.01" id="m-prod-sell" class="form-control" value="${prod.selling_price || ''}" required />
          </div>
          <div class="form-group">
            <label class="form-label">GST Tax Slab *</label>
            <select id="m-prod-gst" class="form-control">
              <option value="0" ${prod.gst_rate === 0 ? 'selected' : ''}>0% (Exempt)</option>
              <option value="5" ${prod.gst_rate === 5 ? 'selected' : ''}>5% (Staples / Groceries)</option>
              <option value="12" ${prod.gst_rate === 12 ? 'selected' : ''}>12% (Packaged Food)</option>
              <option value="18" ${prod.gst_rate === 18 ? 'selected' : ''}>18% (Personal Care)</option>
              <option value="28" ${prod.gst_rate === 28 ? 'selected' : ''}>28% (Luxury / Aerated)</option>
            </select>
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
          <button type="button" class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">${productId ? 'Update Product' : 'Create Product'}</button>
        </div>
      </form>
    `;

    App.openModal();

    document.getElementById('prod-modal-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('m-prod-name').value.trim(),
        tamil_name: document.getElementById('m-prod-tamil').value.trim(),
        category_id: parseInt(document.getElementById('m-prod-cat').value),
        barcode: document.getElementById('m-prod-barcode').value.trim(),
        unit: document.getElementById('m-prod-unit').value,
        purchase_price: parseFloat(document.getElementById('m-prod-buy').value),
        selling_price: parseFloat(document.getElementById('m-prod-sell').value),
        gst_rate: parseFloat(document.getElementById('m-prod-gst').value)
      };

      try {
        if (productId) {
          await API.put(`/api/products/${productId}`, payload);
          showToast('Product SKU updated successfully!', 'success');
        } else {
          await API.post('/api/products', payload);
          showToast('New product created!', 'success');
        }
        App.closeModal();
        await ProductsView.loadProducts();
      } catch (err) {}
    });
  }
};
