// ==============================================================================
// Inventory Management AI: Supplier Intelligence & Performance Scorecards
// ==============================================================================

const SuppliersView = {
  suppliers: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Tamil Nadu Wholesale Supplier Network</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Lead times, fulfillment reliability ratings, return rates, and multi-attribute vendor selection
          </p>
        </div>
      </div>

      <div class="glass-card" style="padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Supplier Name</th>
                <th>District / Location</th>
                <th>Contact Person & Phone</th>
                <th>Avg Lead Time</th>
                <th>Reliability Score</th>
                <th>Defect / Return Rate</th>
                <th>Rating</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="suppliers-table-body">
              <tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Loading suppliers...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await this.loadSuppliers();
  },

  async loadSuppliers() {
    try {
      this.suppliers = await API.get('/api/suppliers');
      const tbody = document.getElementById('suppliers-table-body');
      if (!tbody) return;

      tbody.innerHTML = this.suppliers.map(s => `
        <tr>
          <td>
            <div style="font-weight: 700;">${s.name}</div>
            <div style="font-size: 0.725rem; color: var(--text-muted);">${s.email || ''}</div>
          </td>
          <td>
            <span class="status-badge" style="background: rgba(245, 158, 11, 0.12); color: var(--accent-saffron); border: 1px solid rgba(245, 158, 11, 0.25);">
              📍 ${s.district || 'Tamil Nadu'}
            </span>
          </td>
          <td>
            <div>${s.contact_person || '-'}</div>
            <div style="font-size: 0.725rem; color: var(--text-secondary);">${s.phone || '-'}</div>
          </td>
          <td>
            <span style="font-weight: 700;">${s.avg_lead_time_days} days</span>
          </td>
          <td>
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <div style="flex: 1; height: 6px; width: 60px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <div style="height: 100%; width: ${s.reliability_score}%; background: var(--brand-primary);"></div>
              </div>
              <span style="font-weight: 700; font-size: 0.8rem;">${s.reliability_score}%</span>
            </div>
          </td>
          <td>${s.return_rate}%</td>
          <td>
            <span style="color: var(--accent-saffron); font-weight: 700;">★ ${s.rating.toFixed(1)}</span>
          </td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="SuppliersView.showCatalogModal(${s.id})">
              View Catalog
            </button>
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.error('Failed loading suppliers', e);
    }
  },

  async showCatalogModal(supplierId) {
    try {
      const sup = await API.get(`/api/suppliers/${supplierId}`);
      const modal = document.getElementById('app-modal');

      modal.querySelector('.modal-content').innerHTML = `
        <div class="modal-header">
          <h3 class="modal-title">📦 ${sup.name} - Product Pricing</h3>
          <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
        </div>
        <div style="margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-secondary);">
          <div>Location: <strong>${sup.address || sup.district}</strong> | Lead Time: <strong>${sup.avg_lead_time_days} days</strong></div>
          <div>Reliability: <strong>${sup.reliability_score}%</strong> | Phone: <strong>${sup.phone}</strong></div>
        </div>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Supplied Product</th>
                <th>Supplier Price</th>
                <th>Retail MRP</th>
                <th>Delivery Lead Time</th>
                <th>Min Order Qty (MOQ)</th>
              </tr>
            </thead>
            <tbody>
              ${(sup.products || []).map(p => `
                <tr>
                  <td>
                    <div style="font-weight: 600;">${p.product_name}</div>
                    <div style="font-size: 0.725rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
                  </td>
                  <td style="font-weight: 700; color: var(--brand-primary);">${formatINR(p.supplier_price)}</td>
                  <td>${formatINR(p.selling_price)}</td>
                  <td>${p.delivery_time_days} days</td>
                  <td>${p.moq} ${p.unit}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <div style="display: flex; justify-content: flex-end; margin-top: 1.25rem;">
          <button class="btn btn-secondary btn-sm" onclick="App.closeModal()">Close</button>
        </div>
      `;

      App.openModal();
    } catch (e) {
      console.error('Failed loading supplier catalog', e);
    }
  }
};
