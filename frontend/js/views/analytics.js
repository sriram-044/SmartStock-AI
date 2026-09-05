// ==============================================================================
// Inventory Management AI: Sales & Profit Analytics Controller
// ==============================================================================

const AnalyticsView = {
  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Sales Velocity & Profit Intelligence</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Average daily sales velocity, gross margins, and Tamil Nadu regional festival demand multipliers
          </p>
        </div>
      </div>

      <!-- Top Velocity & Margins Table -->
      <div class="glass-card" style="margin-bottom: 1.75rem; padding: 0;">
        <div style="padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border-color);">
          <h3 style="font-size: 1.1rem;">Top Moving Products & Profit Margins (Last 30 Days)</h3>
          <p style="color: var(--text-muted); font-size: 0.775rem;">Ranked by sales velocity (Units sold per day)</p>
        </div>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Units Sold (30d)</th>
                <th>Sales Velocity (ADS)</th>
                <th>Revenue Generated</th>
                <th>Gross Margin (%)</th>
                <th>Total Profit</th>
                <th>Current Stock</th>
              </tr>
            </thead>
            <tbody id="velocity-table-body">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading analytics...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tamil Nadu Festivals & Seasonal Calendar -->
      <div class="glass-card">
        <div style="margin-bottom: 1rem;">
          <h3 style="font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
            <span>🪔</span> Tamil Nadu Retail Festival & Seasonality Multipliers
          </h3>
          <p style="color: var(--text-muted); font-size: 0.775rem;">Historical surges incorporated into AI replenishment planning</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;" id="festivals-cards-grid">
          <!-- Festival Cards -->
        </div>
      </div>
    `;

    await this.loadData();
  },

  async loadData() {
    try {
      const [velocity, festRes] = await Promise.all([
        API.get('/api/analytics/velocity', { limit: 15 }),
        fetch('/static/../data/festivals_tn.json').then(r => r.json()).catch(() => [])
      ]);

      // Render velocity table
      const tbody = document.getElementById('velocity-table-body');
      if (tbody && velocity) {
        tbody.innerHTML = velocity.map(p => `
          <tr>
            <td>
              <div style="font-weight: 700;">${p.name}</div>
              <div style="font-size: 0.725rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
            </td>
            <td><strong>${p.total_units_30d}</strong> ${p.unit}</td>
            <td>
              <span style="font-weight: 700; color: var(--brand-primary); font-size: 0.95rem;">
                ${p.avg_daily_sales} ${p.unit}/day
              </span>
            </td>
            <td>${formatINR(p.total_revenue_30d)}</td>
            <td>
              <span class="status-badge ${p.margin_pct >= 20 ? 'badge-safe' : 'badge-monitor'}">
                ${p.margin_pct}%
              </span>
            </td>
            <td style="font-weight: 700; color: var(--brand-primary);">${formatINR(p.total_profit_30d)}</td>
            <td>${p.current_stock} ${p.unit}</td>
          </tr>
        `).join('');
      }

      // Render Festival Cards
      const fGrid = document.getElementById('festivals-cards-grid');
      if (fGrid && festRes) {
        fGrid.innerHTML = festRes.map(f => `
          <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: var(--border-radius-md); padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
              <div>
                <div style="font-weight: 700; font-size: 0.95rem;">${f.name}</div>
                <div style="font-size: 0.8rem; color: var(--accent-saffron);">${f.tamil_name || ''}</div>
              </div>
              <span class="status-badge badge-warning">
                +${Math.round((f.demand_multiplier - 1) * 100)}% Surge
              </span>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              Timing: Month ${f.month}, Duration: ${f.duration_days} days
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.35;">
              ${f.notes}
            </div>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error('Failed loading analytics data', e);
    }
  }
};
