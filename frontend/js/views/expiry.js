// ==============================================================================
// Inventory Management AI: FEFO Expiry & Markdown Optimization Controller
// ==============================================================================

const ExpiryView = {
  expiryData: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem; font-weight: 900; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>⏳</span> FEFO Expiry & Shelf-Life Intelligence
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            First-Expired-First-Out batch tracking, unsold loss projections, and markdown clearance triggers
          </p>
        </div>
      </div>

      <!-- Expiry Cards Timeline Grid -->
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem;" id="expiry-cards-grid">
        <p style="color: var(--text-muted); font-size: 0.85rem;">Loading perishable batch trackers...</p>
      </div>
    `;

    await this.loadExpiryData();
  },

  async loadExpiryData() {
    try {
      this.expiryData = await API.get('/api/ai/expiry', { days: 60 });
      const grid = document.getElementById('expiry-cards-grid');
      if (!grid) return;

      if (this.expiryData.length === 0) {
        grid.innerHTML = `
          <div class="glass-card" style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #15803D;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
            <h3 style="font-size: 1.15rem; font-weight: 800;">All Perishable Batches Safe</h3>
            <p style="color: var(--text-muted); font-size: 0.85rem;">
              No inventory expiring within the next 60 days.
            </p>
          </div>
        `;
        return;
      }

      grid.innerHTML = this.expiryData.map(b => {
        const isCritical = b.days_to_expiry <= 15;
        const isWarning = b.days_to_expiry > 15 && b.days_to_expiry <= 30;
        const badgeClass = isCritical ? 'badge-critical' : (isWarning ? 'badge-warning' : 'badge-safe');

        return `
          <div class="glass-card" style="display: flex; flex-direction: column; gap: 0.85rem; border-left: 5px solid ${isCritical ? '#EF4444' : (isWarning ? '#F59E0B' : '#22C55E')};">
            <!-- Top Row -->
            <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem;">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 44px; height: 44px; flex-shrink: 0; background: #F9FAFB; border-radius: 10px; border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; padding: 3px;">
                  ${Assets.getProductImage(b.product_name, '')}
                </div>
                <div>
                  <div style="font-weight: 800; font-size: 0.95rem; color: var(--text-primary); line-height: 1.2;">${b.product_name}</div>
                  <div style="font-size: 0.725rem; color: var(--brand-primary); font-weight: 600;">${b.tamil_name || ''}</div>
                </div>
              </div>
              <span class="status-badge ${badgeClass}" style="font-size: 0.68rem;">
                ${b.days_to_expiry} Days Left
              </span>
            </div>

            <!-- Batch & Date Info -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; background: #F9FAFB; padding: 0.75rem; border-radius: var(--border-radius-md); border: 1px solid var(--border-color); font-size: 0.775rem;">
              <div>
                <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Batch #:</span>
                <div style="font-family: var(--font-mono); font-weight: 700;">${b.batch_number}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Expiry Date:</span>
                <div style="font-weight: 700; color: ${isCritical ? '#DC2626' : 'inherit'};">${b.expiry_date}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Batch Stock:</span>
                <div style="font-weight: 800;">${b.remaining_qty} ${b.unit}</div>
              </div>
              <div>
                <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Unsold Loss (₹):</span>
                <div style="font-weight: 800; color: #DC2626;">${formatINR(b.potential_loss_inr)}</div>
              </div>
            </div>

            <!-- AI Action Recommendation -->
            <div style="padding: 0.65rem 0.85rem; background: #FFF5F5; border: 1px solid rgba(239, 68, 68, 0.15); border-radius: var(--border-radius-md); font-size: 0.8rem; color: #991B1B; line-height: 1.35;">
              <strong>💡 AI Markdown Action:</strong> ${b.recommended_action}
            </div>

            <div style="display: flex; gap: 0.5rem; margin-top: auto;">
              <button class="btn btn-warning btn-sm" style="flex: 1;" onclick="showToast('Markdown clearance tag applied to POS terminal', 'success')">
                🏷️ Apply Markdown
              </button>
              <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="App.navigate('inventory')">
                📑 Ledger
              </button>
            </div>
          </div>
        `;
      }).join('');
    } catch (e) {
      console.error('Failed loading expiry batches', e);
    }
  }
};
