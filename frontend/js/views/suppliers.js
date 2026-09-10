// ==============================================================================
// Inventory Management AI: Supplier Intelligence & Vendor Cards Controller
// ==============================================================================

const SuppliersView = {
  suppliers: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem; font-weight: 900; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>🚚</span> Tamil Nadu Wholesale Supplier Network
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Delivery lead times, fulfillment reliability ratings, wholesale prices, and vendor scorecards
          </p>
        </div>
      </div>

      <!-- Supplier Cards Grid -->
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem;" id="suppliers-cards-grid">
        <p style="color: var(--text-muted); font-size: 0.85rem;">Loading supplier network...</p>
      </div>
    `;

    await this.loadSuppliers();
  },

  async loadSuppliers() {
    try {
      this.suppliers = await API.get('/api/suppliers');
      const grid = document.getElementById('suppliers-cards-grid');
      if (!grid) return;

      grid.innerHTML = this.suppliers.map((s, index) => {
        const isTop = index === 0 || s.reliability_score >= 95;
        return `
          <div class="glass-card" style="display: flex; flex-direction: column; gap: 1rem; position: relative;">
            ${isTop ? `
              <div style="position: absolute; top: 1rem; right: 1rem;">
                <span class="status-badge badge-safe" style="font-size: 0.68rem;">
                  🏆 Best Supplier
                </span>
              </div>
            ` : ''}

            <!-- Supplier Header -->
            <div style="display: flex; align-items: center; gap: 0.85rem;">
              <div style="width: 48px; height: 48px; border-radius: 12px; background: var(--gradient-ai-red); color: #FFFFFF; font-weight: 800; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(230, 57, 70, 0.2);">
                ${s.name.charAt(0)}
              </div>
              <div style="flex: 1; padding-right: ${isTop ? '90px' : '0'};">
                <div style="font-weight: 800; font-size: 1rem; color: var(--text-primary); line-height: 1.2;">
                  ${s.name}
                </div>
                <div style="margin-top: 0.2rem;">
                  <span class="status-badge" style="background: #FEF3C7; color: #B45309; font-size: 0.68rem; padding: 0.1rem 0.45rem;">
                    📍 ${s.district || 'Tamil Nadu'}
                  </span>
                </div>
              </div>
            </div>

            <!-- Metrics Grid -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; background: #F9FAFB; padding: 0.85rem; border-radius: var(--border-radius-md); border: 1px solid var(--border-color); font-size: 0.775rem;">
              <div>
                <span style="color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Rating:</span>
                <div style="color: #D97706; font-weight: 800; font-size: 0.95rem;">★ ${s.rating.toFixed(1)} / 5.0</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Lead Time:</span>
                <div style="font-weight: 800; font-size: 0.95rem; color: var(--text-primary);">${s.avg_lead_time_days} Days</div>
              </div>
              <div style="grid-column: 1 / -1;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                  <span style="color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Reliability Score:</span>
                  <strong style="color: #15803D;">${s.reliability_score}%</strong>
                </div>
                <div style="height: 6px; background: #E5E7EB; border-radius: 9999px; overflow: hidden;">
                  <div style="height: 100%; width: ${s.reliability_score}%; background: #22C55E;"></div>
                </div>
              </div>
            </div>

            <!-- Contact Line -->
            <div style="font-size: 0.775rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.15rem;">
              <div>👤 Contact: <strong>${s.contact_person || 'Sales Department'}</strong></div>
              <div>📞 Phone: <strong>${s.phone || '+91 98400 00000'}</strong></div>
            </div>

            <!-- Action Button -->
            <div style="margin-top: auto; padding-top: 0.5rem;">
              <button class="btn btn-secondary btn-sm" style="width: 100%;" onclick="SuppliersView.showCatalogModal(${s.id})">
                📦 View Products & Wholesale Catalog
              </button>
            </div>
          </div>
        `;
      }).join('');
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
          <h3 class="modal-title">📦 ${sup.name} &mdash; Wholesale Catalog</h3>
          <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
        </div>
        <div style="margin-bottom: 1rem; font-size: 0.85rem; color: var(--text-secondary);">
          <div>Location: <strong>${sup.address || sup.district}</strong> &bull; Lead Time: <strong>${sup.avg_lead_time_days} days</strong></div>
          <div>Reliability: <strong>${sup.reliability_score}%</strong> &bull; Phone: <strong>${sup.phone}</strong></div>
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
                    <div style="font-weight: 700;">${p.product_name}</div>
                    <div style="font-size: 0.725rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
                  </td>
                  <td style="font-weight: 800; color: #15803D;">${formatINR(p.supplier_price)}</td>
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
