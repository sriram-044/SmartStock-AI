// ==============================================================================
// Inventory Management AI: Demand Forecasting & ML Model Comparison Controller
// ==============================================================================

const ForecastingView = {
  products: [],
  selectedProductId: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Machine Learning Demand Forecasting</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Comparative evaluation of Moving Average, Linear Regression, and Random Forest models
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <label class="form-label" style="margin: 0;">Select Product:</label>
          <select id="forecast-prod-select" class="form-control" style="width: 280px;">
            <option value="">Loading products...</option>
          </select>
        </div>
      </div>

      <!-- Forecast Horizons Cards -->
      <div class="kpi-grid" id="forecast-kpis-grid">
        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span>Next 1-Day Demand</span>
            <div class="kpi-icon-wrap kpi-icon-emerald">📅</div>
          </div>
          <div class="kpi-value" id="fc-1d">...</div>
          <div class="kpi-footer">Projected tomorrow</div>
        </div>

        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span>Next 7-Day Demand</span>
            <div class="kpi-icon-wrap kpi-icon-saffron">📊</div>
          </div>
          <div class="kpi-value" id="fc-7d">...</div>
          <div class="kpi-footer">Weekly replenishment buffer</div>
        </div>

        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span>Next 30-Day Demand</span>
            <div class="kpi-icon-wrap kpi-icon-purple">📈</div>
          </div>
          <div class="kpi-value" id="fc-30d">...</div>
          <div class="kpi-footer">Monthly inventory projection</div>
        </div>

        <div class="glass-card kpi-card">
          <div class="kpi-header">
            <span>Selected ML Model</span>
            <div class="kpi-icon-wrap kpi-icon-cyan">🧠</div>
          </div>
          <div class="kpi-value" id="fc-model" style="font-size: 1.15rem;">...</div>
          <div class="kpi-footer">
            <span>Validation MAE: <strong id="fc-mae">...</strong></span>
          </div>
        </div>
      </div>

      <!-- Forecast Chart & Model Benchmark -->
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem;">
        <!-- 30-Day Projected Demand Curve -->
        <div class="glass-card" style="display: flex; flex-direction: column;">
          <div style="margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem;">30-Day Autoregressive Demand Projection</h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Simulated forward daily sales with calendar & trend dynamics</p>
          </div>
          <div style="flex: 1; position: relative;">
            <canvas id="chart-forecast-curve" style="width: 100%; height: 260px;"></canvas>
          </div>
        </div>

        <!-- ML Model Performance Comparison -->
        <div class="glass-card">
          <div style="margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem;">Cross-Validation Benchmark</h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Holdout error comparison on recent sales</p>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>MAE</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody id="fc-models-table">
                <tr><td colspan="3" style="text-align: center; color: var(--text-muted);">Evaluating...</td></tr>
              </tbody>
            </table>
          </div>
          <div style="margin-top: 1rem; font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;">
            * The engine dynamically chooses the algorithm with the lowest validation Mean Absolute Error (MAE) per SKU.
          </div>
        </div>
      </div>
    `;

    await this.loadProducts();
  },

  async loadProducts() {
    try {
      const res = await API.get('/api/products', { limit: 100 });
      this.products = res.items || [];
      const select = document.getElementById('forecast-prod-select');
      if (!select) return;

      select.innerHTML = this.products.map(p => `
        <option value="${p.id}">${p.name} (${p.unit})</option>
      `).join('');

      select.addEventListener('change', (e) => {
        this.selectedProductId = parseInt(e.target.value);
        this.loadForecast();
      });

      if (this.products.length > 0) {
        this.selectedProductId = this.products[0].id;
        await this.loadForecast();
      }
    } catch (e) {
      console.error('Failed loading forecast products', e);
    }
  },

  async loadForecast() {
    if (!this.selectedProductId) return;
    try {
      const fc = await API.get(`/api/ai/forecast/${this.selectedProductId}`);
      const prod = this.products.find(p => p.id === this.selectedProductId);
      const unit = prod ? prod.unit : 'units';

      document.getElementById('fc-1d').innerText = `${fc.forecast_1d} ${unit}`;
      document.getElementById('fc-7d').innerText = `${fc.forecast_7d} ${unit}`;
      document.getElementById('fc-30d').innerText = `${fc.forecast_30d} ${unit}`;
      document.getElementById('fc-model').innerText = fc.selected_model;
      document.getElementById('fc-mae').innerText = `${fc.validation_mae} ${unit}`;

      // Render chart
      Charts.renderForecastChart('chart-forecast-curve', fc.daily_projections, fc.avg_daily_sales);

      // Render Models comparison table
      const tbody = document.getElementById('fc-models-table');
      if (tbody && fc.model_comparison) {
        tbody.innerHTML = fc.model_comparison.map(m => `
          <tr>
            <td style="font-weight: 600;">${m.model || m.model_name}</td>
            <td>${m.mae}</td>
            <td>
              <span class="status-badge ${m.status.includes('Selected') ? 'badge-safe' : 'badge-monitor'}" style="font-size: 0.65rem;">
                ${m.status.includes('Selected') ? 'Best Fit' : 'Evaluated'}
              </span>
            </td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.error('Failed loading forecast data', e);
    }
  }
};
