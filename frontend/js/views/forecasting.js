// ==============================================================================
// Inventory Management AI: Demand Forecasting & ML Model Comparison Controller
// ==============================================================================

const ForecastingView = {
  products: [],
  selectedProductId: null,
  activeHorizon: 30,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <h2 style="font-size: 1.4rem; font-weight: 900; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>📈</span> Machine Learning Demand Forecasting
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Comparative evaluation of Moving Average, Linear Regression, and Random Forest models
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <label class="form-label" style="margin: 0; font-weight: 700;">Select Product:</label>
          <select id="forecast-prod-select" class="form-control" style="width: 280px;">
            <option value="">Loading products...</option>
          </select>
        </div>
      </div>

      <!-- Forecast Horizons KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap" style="background: #DCFCE7; color: #15803D;">📅</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Next 1-Day Demand</span>
              <div class="kpi-value" id="fc-1d">...</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">Tomorrow</span>
            <span>Projected daily pickup</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap" style="background: #FEF3C7; color: #B45309;">📊</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Next 7-Day Demand</span>
              <div class="kpi-value" id="fc-7d">...</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">Weekly Buffer</span>
            <span>Supplier order window</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap" style="background: #EDE9FE; color: #7C3AED;">📈</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Next 30-Day Demand</span>
              <div class="kpi-value" id="fc-30d">...</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">Monthly</span>
            <span>Total forward demand</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap" style="background: #E0E7FF; color: #4338CA;">🧠</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Selected Model</span>
              <div class="kpi-value" id="fc-model" style="font-size: 1.15rem;">...</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span>Validation MAE: <strong id="fc-mae" style="color: #15803D;">...</strong></span>
          </div>
        </div>
      </div>

      <!-- Forecast Chart & Model Benchmark -->
      <div style="display: grid; grid-template-columns: 2fr 1.2fr; gap: 1.5rem;">
        <!-- Projected Demand Curve -->
        <div class="glass-card" style="display: flex; flex-direction: column;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
              <h3 style="font-size: 1.05rem; font-weight: 800;">30-Day Autoregressive Demand Projection</h3>
              <p style="color: var(--text-muted); font-size: 0.775rem;">Simulated forward daily sales with calendar & festival dynamics</p>
            </div>
          </div>
          <div style="flex: 1; min-height: 250px; position: relative;">
            <canvas id="chart-forecast-curve" style="width: 100%; height: 260px;"></canvas>
          </div>
        </div>

        <!-- ML Model Performance Comparison -->
        <div class="glass-card">
          <div style="margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
            <h3 style="font-size: 1.05rem; font-weight: 800;">Cross-Validation Benchmark</h3>
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
                <tr><td colspan="3" style="text-align: center; color: var(--text-muted);">Evaluating algorithms...</td></tr>
              </tbody>
            </table>
          </div>
          <div style="margin-top: 1rem; padding: 0.75rem; background: #F9FAFB; border-radius: 8px; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4;">
            💡 <strong>Dynamic Selector:</strong> The forecasting engine evaluates all 3 algorithms on holdout data and automatically chooses the model with lowest Mean Absolute Error (MAE) per SKU.
          </div>
        </div>
      </div>
    `;

    await this.loadProducts();
  },

  async loadProducts() {
    try {
      const res = await API.get('/api/products', { limit: 150 });
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
        tbody.innerHTML = fc.model_comparison.map(m => {
          const isBest = m.status.includes('Selected') || m.model.includes(fc.selected_model);
          return `
            <tr>
              <td style="font-weight: 700;">${m.model || m.model_name}</td>
              <td style="font-weight: 800;">${m.mae}</td>
              <td>
                <span class="status-badge ${isBest ? 'badge-safe' : 'badge-monitor'}" style="font-size: 0.65rem;">
                  ${isBest ? '🏆 BEST MODEL' : 'Evaluated'}
                </span>
              </td>
            </tr>
          `;
        }).join('');
      }
    } catch (e) {
      console.error('Failed loading forecast data', e);
    }
  }
};
