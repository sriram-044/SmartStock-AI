// ==============================================================================
// Inventory Management AI: FEFO Expiry & Markdown Optimization Controller
// ==============================================================================

const ExpiryView = {
  expiryData: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">FEFO Expiry & Shelf-Life Intelligence</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            First-Expired-First-Out batch tracking, unsold loss projections, and markdown clearance triggers
          </p>
        </div>
      </div>

      <div class="glass-card" style="padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product & Batch #</th>
                <th>Expiry Date</th>
                <th>Days Remaining</th>
                <th>Stock in Batch</th>
                <th>Projected Unsold Loss (₹)</th>
                <th>Risk Status</th>
                <th>AI Action Recommendation</th>
              </tr>
            </thead>
            <tbody id="expiry-table-body">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading FEFO expiry batches...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await this.loadExpiryData();
  },

  async loadExpiryData() {
    try {
      this.expiryData = await API.get('/api/ai/expiry', { days: 60 });
      const tbody = document.getElementById('expiry-table-body');
      if (!tbody) return;

      if (this.expiryData.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--status-safe);">
              ✅ All perishable batches have safe shelf-life remaining (> 60 days).
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = this.expiryData.map(b => {
        const isCritical = b.risk_status === 'CRITICAL_EXPIRY';
        return `
          <tr>
            <td>
              <div style="font-weight: 700;">${b.product_name}</div>
              <div style="font-size: 0.725rem; color: var(--brand-primary);">${b.tamil_name || ''}</div>
              <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted);">Batch: ${b.batch_number}</div>
            </td>
            <td>${b.expiry_date}</td>
            <td>
              <span style="font-weight: 800; font-size: 1.05rem; color: ${isCritical ? 'var(--status-critical)' : 'var(--accent-saffron)'};">
                ${b.days_to_expiry} days
              </span>
            </td>
            <td>
              <span style="font-weight: 700;">${b.remaining_qty} ${b.unit}</span>
              <div style="font-size: 0.7rem; color: var(--text-muted);">ADS: ${b.avg_daily_sales} ${b.unit}/day</div>
            </td>
            <td>
              <div style="font-weight: 700; color: var(--status-critical); font-size: 0.95rem;">
                ${formatINR(b.potential_loss_inr)}
              </div>
              <div style="font-size: 0.7rem; color: var(--text-muted);">At risk: ~${b.unsold_units_at_risk} ${b.unit}</div>
            </td>
            <td>
              <span class="status-badge badge-${isCritical ? 'critical' : 'warning'}">
                <span class="badge-dot"></span> ${b.status_label}
              </span>
            </td>
            <td>
              <div style="font-size: 0.8rem; color: var(--text-primary); line-height: 1.3;">
                ${b.recommended_action}
              </div>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error('Failed loading expiry batches', e);
    }
  }
};
