// ==============================================================================
// Inventory Management AI: Dashboard View Controller
// ==============================================================================

const DashboardView = {
  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Executive Inventory & AI Dashboard</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Real-time stock monitoring, sales velocity, and automated agent replenishment recommendations
          </p>
        </div>
        <button id="btn-run-agent" class="btn btn-primary">
          <span>⚡</span>
          <span data-i18n="btn_scan_ai">Run Agent Scan</span>
        </button>
      </div>

      <!-- KPI Stat Cards -->
      <div class="kpi-grid">
        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span data-i18n="kpi_inventory_val">Inventory Valuation</span>
            <div class="kpi-icon-wrap kpi-icon-emerald">₹</div>
          </div>
          <div class="kpi-value" id="kpi-inventory-val">...</div>
          <div class="kpi-footer">
            <span>Total Units: <strong id="kpi-inventory-qty">...</strong></span>
          </div>
        </div>

        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span data-i18n="kpi_today_sales">Today's Sales</span>
            <div class="kpi-icon-wrap kpi-icon-saffron">🛒</div>
          </div>
          <div class="kpi-value" id="kpi-today-sales">...</div>
          <div class="kpi-footer">
            <span class="kpi-trend-up" id="kpi-today-orders">...</span> orders today
          </div>
        </div>

        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span data-i18n="kpi_today_profit">Today's Gross Profit</span>
            <div class="kpi-icon-wrap kpi-icon-cyan">📈</div>
          </div>
          <div class="kpi-value" id="kpi-today-profit">...</div>
          <div class="kpi-footer">
            <span>Month Sales: <strong id="kpi-month-sales">...</strong></span>
          </div>
        </div>

        <div class="glass-card kpi-card" style="cursor: pointer;" onclick="App.navigate('ai-recom')">
          <div class="kpi-header">
            <span data-i18n="kpi_pending_recom">Pending AI Actions</span>
            <div class="kpi-icon-wrap kpi-icon-purple">🤖</div>
          </div>
          <div class="kpi-value" id="kpi-pending-recom" style="color: var(--accent-saffron);">...</div>
          <div class="kpi-footer">
            <span id="kpi-critical-stock" class="status-badge badge-critical">...</span>
          </div>
        </div>
      </div>

      <!-- Visual Analytics Grid -->
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; margin-bottom: 1.75rem;">
        <!-- Sales & Profit 30-Day Trend Chart -->
        <div class="glass-card" style="min-height: 330px; display: flex; flex-direction: column;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
              <h3 style="font-size: 1.05rem;">Sales Revenue vs. Profit Trend (30 Days)</h3>
              <p style="color: var(--text-muted); font-size: 0.775rem;">Aggregated POS transactions & gross profit margin</p>
            </div>
            <div style="display: flex; gap: 1rem; font-size: 0.75rem; font-weight: 600;">
              <span style="display: flex; align-items: center; gap: 0.35rem; color: #10B981;">
                <span style="width: 10px; height: 10px; background: #10B981; border-radius: 2px;"></span> Revenue
              </span>
              <span style="display: flex; align-items: center; gap: 0.35rem; color: #06B6D4;">
                <span style="width: 10px; height: 10px; background: #06B6D4; border-radius: 2px;"></span> Gross Profit
              </span>
            </div>
          </div>
          <div style="flex: 1; position: relative;">
            <canvas id="chart-sales-trend" style="width: 100%; height: 250px;"></canvas>
          </div>
        </div>

        <!-- Stock Risk Distribution Donut Chart -->
        <div class="glass-card" style="min-height: 330px; display: flex; flex-direction: column;">
          <div style="margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem;">Inventory Risk Breakdown</h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Stockout vs safety buffer classification</p>
          </div>
          <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
            <canvas id="chart-risk-donut" style="width: 100%; max-width: 220px; height: 200px;"></canvas>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem;">
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#10B981;"></span> Safe Stock: <b id="lbl-safe">0</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#3B82F6;"></span> Reorder Soon: <b id="lbl-low">0</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#EF4444;"></span> Critical: <b id="lbl-critical">0</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#F59E0B;"></span> Overstock: <b id="lbl-over">0</b></div>
          </div>
        </div>
      </div>

      <!-- Quick Action / Urgent Replenishments -->
      <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h3 style="font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
            <span>🚨</span> Urgent Agent Replenishment Recommendations
          </h3>
          <button class="btn btn-secondary btn-sm" onclick="App.navigate('ai-recom')">
            View All AI Recommendations →
          </button>
        </div>
        <div id="urgent-recom-list">
          <p style="color: var(--text-muted); font-size: 0.85rem;">Loading AI recommendations...</p>
        </div>
      </div>
    `;

    document.getElementById('btn-run-agent').addEventListener('click', async () => {
      const btn = document.getElementById('btn-run-agent');
      btn.innerHTML = '<span>⏳</span> Scanning Catalog...';
      btn.disabled = true;
      try {
        const res = await API.post('/api/ai/scan');
        showToast(`AI Scan complete: ${res.new_or_updated_recommendations} recommendations evaluated!`, 'success');
        await DashboardView.loadData();
      } finally {
        btn.innerHTML = '<span>⚡</span> Run Agent Scan';
        btn.disabled = false;
      }
    });

    await this.loadData();
  },

  async loadData() {
    try {
      const [kpis, trend, recoms] = await Promise.all([
        API.get('/api/analytics/dashboard'),
        API.get('/api/analytics/sales-trend', { days: 30 }),
        API.get('/api/ai/recommendations', { status: 'PENDING' })
      ]);

      // Populate KPIs
      document.getElementById('kpi-inventory-val').innerText = formatINR(kpis.total_inventory_value);
      document.getElementById('kpi-inventory-qty').innerText = `${kpis.total_inventory_qty} units`;
      document.getElementById('kpi-today-sales').innerText = formatINR(kpis.today_sales);
      document.getElementById('kpi-today-orders').innerText = kpis.today_orders;
      document.getElementById('kpi-today-profit').innerText = formatINR(kpis.today_profit);
      document.getElementById('kpi-month-sales').innerText = formatINR(kpis.month_sales, true);
      document.getElementById('kpi-pending-recom').innerText = kpis.pending_recom_count;
      document.getElementById('kpi-critical-stock').innerText = `${kpis.critical_stock_count} Critical`;

      // Render Charts
      Charts.renderSalesTrend('chart-sales-trend', trend);
      Charts.renderRiskDonut('chart-risk-donut', {
        safe: kpis.safe_stock_count,
        low: kpis.low_stock_count,
        critical: kpis.critical_stock_count,
        overstock: kpis.overstock_count
      });

      document.getElementById('lbl-safe').innerText = kpis.safe_stock_count;
      document.getElementById('lbl-low').innerText = kpis.low_stock_count;
      document.getElementById('lbl-critical').innerText = kpis.critical_stock_count;
      document.getElementById('lbl-over').innerText = kpis.overstock_count;

      // Urgent Recoms list
      const urgentContainer = document.getElementById('urgent-recom-list');
      if (!recoms || recoms.length === 0) {
        urgentContainer.innerHTML = `
          <div style="padding: 1.5rem; text-align: center; color: var(--status-safe);">
            <p>✅ All products are well-stocked. No immediate restock actions required.</p>
          </div>
        `;
        return;
      }

      urgentContainer.innerHTML = recoms.slice(0, 3).map(r => `
        <div class="recom-card risk-${r.risk_level}" style="padding: 1rem; margin-bottom: 0.75rem;">
          <div class="recom-top">
            <div class="recom-title-wrap">
              <div class="recom-prod-name">${r.product_name}</div>
              <div class="recom-tamil-name">${r.tamil_name || ''}</div>
            </div>
            <span class="status-badge badge-${r.risk_level === 'CRITICAL' ? 'critical' : 'warning'}">
              <span class="badge-dot"></span> ${r.risk_level.replace('_', ' ')}
            </span>
          </div>
          <div class="recom-reasoning" style="padding: 0.6rem 0.85rem; font-size: 0.8rem;">
            ${r.rationale}
          </div>
          <div class="recom-actions" style="padding-top: 0.35rem;">
            <span style="margin-right: auto; font-size: 0.8rem; color: var(--text-secondary);">
              Suggested Supplier: <strong>${r.supplier_name || 'Direct Wholesale'}</strong>
            </span>
            <button class="btn btn-primary btn-sm" onclick="App.approveRecommendation(${r.id})">
              Approve (${r.recommended_qty} ${r.unit})
            </button>
          </div>
        </div>
      `).join('');

    } catch (e) {
      console.error('Failed loading dashboard data', e);
    }
  }
};
