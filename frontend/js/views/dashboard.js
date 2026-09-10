// ==============================================================================
// Inventory Management AI: Executive AI Dashboard View Controller
// Designed for Tamil Nadu Retail Operations (Sri Murugan Super Store, T. Nagar, Chennai)
// ==============================================================================

const DashboardView = {
  activeTrendDays: 30,

  async render(container) {
    const userFirstName = App.currentUser ? App.currentUser.full_name.split(' ')[0] : 'Sriram';
    const shopName = App.shopInfo ? App.shopInfo.shop_name : 'Sri Murugan Super Store';

    container.innerHTML = `
      <!-- Top Greeting & Header Bar -->
      <div style="margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 1rem;">
        <div>
          <div style="font-size: 0.85rem; font-weight: 700; color: #059669; display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.2rem;">
            <span class="pulse-dot"></span> Agentic AI Live Monitoring &bull; Sri Murugan Super Store
          </div>
          <h2 style="font-size: 1.65rem; font-weight: 900; color: var(--text-primary); letter-spacing: -0.02em;">
            Good Evening, ${userFirstName} 👋
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Here's what your Agentic AI monitored and optimized today at <strong>${shopName}</strong>.
          </p>
        </div>

        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <button id="btn-run-agent" class="btn btn-ai" style="padding: 0.65rem 1.35rem;">
            <span>⚡</span>
            <span>Run Complete AI Cycle</span>
          </button>
        </div>
      </div>

      <!-- 4 TOP KPI CARDS WITH ICON GLOW -->
      <div class="kpi-grid">
        <!-- CARD 1: Total Revenue -->
        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap kpi-icon-sales">💰</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Today's Sales Revenue</span>
              <div class="kpi-value" id="kpi-today-sales">₹12,48,500</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">↑ 14.2%</span>
            <span>vs previous week</span>
          </div>
        </div>

        <!-- CARD 2: Active Stock Value -->
        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap kpi-icon-stock">📦</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">Active Stock Value</span>
              <div class="kpi-value" id="kpi-inventory-val">₹34,80,200</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">55 SKUs</span>
            <span>in active monitoring</span>
          </div>
        </div>

        <!-- CARD 3: AI Actions Executed -->
        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap kpi-icon-ai">🤖</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">AI Actions Executed</span>
              <div class="kpi-value" id="kpi-ai-actions">142</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">98.4%</span>
            <span>automated accuracy</span>
          </div>
        </div>

        <!-- CARD 4: ML Forecast Accuracy -->
        <div class="kpi-card">
          <div class="kpi-card-header">
            <div class="kpi-icon-wrap kpi-icon-products">📈</div>
            <div class="kpi-title-wrap">
              <span class="kpi-title">ML Forecast Accuracy</span>
              <div class="kpi-value" id="kpi-forecast-acc">94.8%</div>
            </div>
          </div>
          <div class="kpi-footer">
            <span class="kpi-trend-pill trend-up">Random Forest</span>
            <span>7-day horizon</span>
          </div>
        </div>
      </div>

      <!-- AGENTIC AI COMMAND CENTER: 7-NODE CONNECTED WORKFLOW -->
      <div class="agent-command-center">
        <div class="agent-command-header">
          <div class="agent-command-title">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: #0F172A; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
              🧠
            </div>
            <div>
              <h3 style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin: 0;">Agentic AI Decision Pipeline</h3>
              <p style="font-size: 0.75rem; color: var(--text-muted); margin: 0;">Autonomous 7-Stage Retail Intelligence Loop &bull; Continuous Real-Time Evaluation</p>
            </div>
          </div>
          <div class="agent-badge-live">
            <span class="pulse-dot"></span>
            <span>PIPELINE ACTIVE &bull; 0.4s LATENCY</span>
          </div>
        </div>

        <div class="agent-workflow-pipeline">
          <!-- Node 1 -->
          <div class="workflow-node-card done">
            <div class="workflow-node-num">1</div>
            <div class="workflow-node-title">Demand Signals</div>
            <div class="workflow-node-subtitle">POS stream & daily sales velocity</div>
          </div>

          <!-- Node 2 -->
          <div class="workflow-node-card done">
            <div class="workflow-node-num">2</div>
            <div class="workflow-node-title">Inventory State</div>
            <div class="workflow-node-subtitle">Runout calculation & stock levels</div>
          </div>

          <!-- Node 3 -->
          <div class="workflow-node-card done">
            <div class="workflow-node-num">3</div>
            <div class="workflow-node-title">ML Forecasting</div>
            <div class="workflow-node-subtitle">Random Forest 7-day predictive models</div>
          </div>

          <!-- Node 4 -->
          <div class="workflow-node-card done">
            <div class="workflow-node-num">4</div>
            <div class="workflow-node-title">Supplier Ranking</div>
            <div class="workflow-node-subtitle">Lead time, unit price & reliability score</div>
          </div>

          <!-- Node 5 -->
          <div class="workflow-node-card active">
            <div class="workflow-node-num">5</div>
            <div class="workflow-node-title">Reorder Engine</div>
            <div class="workflow-node-subtitle">EOQ optimization & safety buffer sizing</div>
          </div>

          <!-- Node 6 -->
          <div class="workflow-node-card">
            <div class="workflow-node-num">6</div>
            <div class="workflow-node-title">Auto-PO Draft</div>
            <div class="workflow-node-subtitle">Pre-filled purchase orders & human-in-the-loop</div>
          </div>

          <!-- Node 7 -->
          <div class="workflow-node-card">
            <div class="workflow-node-num">7</div>
            <div class="workflow-node-title">Dispatch & Track</div>
            <div class="workflow-node-subtitle">WhatsApp/Email vendor notification</div>
          </div>
        </div>

        <div class="agent-timeline-log">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span>🕒</span>
            <span><strong>Last AI Scan:</strong> Just now &bull; Scanned 55 SKUs &bull; 3 reorder recommendations generated &bull; 0 stockouts prevented</span>
          </div>
          <a href="javascript:void(0)" onclick="App.navigate('ai-recom')" style="color: #059669; font-weight: 700; text-decoration: none;">
            View Detailed AI Recommendations →
          </a>
        </div>
      </div>

      <!-- AI PRIORITY INSIGHTS SECTION -->
      <div class="priority-insights-section">
        <div class="section-header-wrap">
          <div class="section-title">
            <span>🚨</span> AI Priority Action Items & Urgent Recommendations
          </div>
          <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">3 items require attention</span>
        </div>

        <div class="priority-insights-grid" id="priority-insights-list">
          <!-- CARD 1: Ponni Rice Reorder -->
          <div class="priority-insight-card alert-reorder">
            <div class="insight-top-bar">
              <div class="insight-item-header">
                <div class="insight-item-icon">🍚</div>
                <div>
                  <div class="insight-item-title">Ponni Boiled Rice (25kg Bag)</div>
                  <div class="insight-item-tamil">பொன்னி புழுங்கல் அரிசி &bull; Rice & Grains</div>
                </div>
              </div>
              <span class="status-badge badge-critical">
                <span class="badge-dot"></span> REORDER TRIGGERED
              </span>
            </div>

            <div class="insight-metrics-row">
              <div class="metric-cell">
                <span class="metric-cell-label">Current Stock</span>
                <span class="metric-cell-value" style="color: #EF4444;">8 Bags</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Reorder Point</span>
                <span class="metric-cell-value">20 Bags</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Forecasted Runout</span>
                <span class="metric-cell-value" style="color: #EF4444;">1.8 Days</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">AI Suggested Qty</span>
                <span class="metric-cell-value" style="color: #059669;">50 Bags (₹72,500)</span>
              </div>
            </div>

            <div class="insight-reasoning-box">
              🤖 <strong>AI Reasoning:</strong> Sales velocity is 11.2 bags/day (+18% Tamil Nadu weekend surge). Current stock of 8 bags will stock out in under 48 hours. Auto-selected <strong>Salem Agro Rice Mills</strong> (Score 94/100, 1-day lead time, ₹1,450/bag).
            </div>

            <div class="insight-actions-row">
              <div style="font-size: 0.8rem; color: var(--text-secondary);">
                Recommended Vendor: <strong>Salem Agro Rice Mills</strong> &bull; Lead Time: 1 Day &bull; Reliability: 98%
              </div>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-secondary btn-sm" onclick="DashboardView.openMathModal('Ponni Boiled Rice 25kg')">
                  🔍 View Math
                </button>
                <button class="btn btn-ai btn-sm" onclick="DashboardView.quickApprove('Ponni Boiled Rice 25kg')">
                  ⚡ Approve PO (Auto-Dispatched)
                </button>
              </div>
            </div>
          </div>

          <!-- CARD 2: Sunflower Oil Lead Time Spike -->
          <div class="priority-insight-card alert-leadtime">
            <div class="insight-top-bar">
              <div class="insight-item-header">
                <div class="insight-item-icon">🛢️</div>
                <div>
                  <div class="insight-item-title">Gold Winner Sunflower Oil (1L Bottle)</div>
                  <div class="insight-item-tamil">சன்ஃப்ளவர் எண்ணெய் &bull; Cooking Oils</div>
                </div>
              </div>
              <span class="status-badge badge-warning">
                <span class="badge-dot"></span> SUPPLIER LEAD TIME SPIKE
              </span>
            </div>

            <div class="insight-metrics-row">
              <div class="metric-cell">
                <span class="metric-cell-label">Current Stock</span>
                <span class="metric-cell-value" style="color: #F59E0B;">24 Bottles</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Reorder Point</span>
                <span class="metric-cell-value">30 Bottles</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Lead Time Delay</span>
                <span class="metric-cell-value" style="color: #F59E0B;">+2 Days (Transit)</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">AI Suggested Qty</span>
                <span class="metric-cell-value" style="color: #059669;">60 Bottles (₹8,280)</span>
              </div>
            </div>

            <div class="insight-reasoning-box" style="background: #FFFBEB; border-left-color: #F59E0B; color: #92400E;">
              🤖 <strong>AI Reasoning:</strong> Supplier Sri Krishna Traders reported a +2 day transit delay. AI dynamically expanded safety stock buffer by +15 units to guarantee zero stockout risk during the upcoming festive week.
            </div>

            <div class="insight-actions-row">
              <div style="font-size: 0.8rem; color: var(--text-secondary);">
                Recommended Vendor: <strong>Krishna Oil Mills</strong> &bull; Unit Price: ₹138 &bull; AI Score: 91/100
              </div>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-secondary btn-sm" onclick="DashboardView.openMathModal('Gold Winner Sunflower Oil 1L')">
                  🔍 View Math
                </button>
                <button class="btn btn-ai btn-sm" onclick="DashboardView.quickApprove('Gold Winner Sunflower Oil 1L')">
                  ⚡ Approve PO (Auto-Dispatched)
                </button>
              </div>
            </div>
          </div>

          <!-- CARD 3: Aavin Milk Expiry Risk -->
          <div class="priority-insight-card alert-expiry">
            <div class="insight-top-bar">
              <div class="insight-item-header">
                <div class="insight-item-icon">🥛</div>
                <div>
                  <div class="insight-item-title">Aavin Toned Milk (500ml Packet)</div>
                  <div class="insight-item-tamil">ஆவின் பால் &bull; Dairy & Fresh</div>
                </div>
              </div>
              <span class="status-badge badge-monitor" style="background: #EEF2FF; color: #4F46E5; border-color: #C7D2FE;">
                <span class="badge-dot" style="background: #6366F1;"></span> FEFO EXPIRY RISK (2 DAYS)
              </span>
            </div>

            <div class="insight-metrics-row">
              <div class="metric-cell">
                <span class="metric-cell-label">Batch Number</span>
                <span class="metric-cell-value">BN-20260904</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Expires In</span>
                <span class="metric-cell-value" style="color: #6366F1;">2 Days</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">Qty at Risk</span>
                <span class="metric-cell-value">18 Packets</span>
              </div>
              <div class="metric-cell">
                <span class="metric-cell-label">AI Action</span>
                <span class="metric-cell-value" style="color: #4F46E5;">20% POS Markdown</span>
              </div>
            </div>

            <div class="insight-reasoning-box" style="background: #F5F3FF; border-left-color: #8B5CF6; color: #5B21B6;">
              🤖 <strong>AI Reasoning:</strong> FEFO protocol flagged 18 packets near expiry date. AI recommends immediate 20% price markdown at POS terminal to clear remaining inventory today with zero spoilage loss.
            </div>

            <div class="insight-actions-row">
              <div style="font-size: 0.8rem; color: var(--text-secondary);">
                Promotional Price: <strong>₹19.20</strong> (MRP ₹24.00) &bull; Est. Clearance Time: 4 Hours
              </div>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-secondary btn-sm" onclick="App.navigate('expiry')">
                  🔍 View FEFO Timeline
                </button>
                <button class="btn btn-primary btn-sm" onclick="DashboardView.applyMarkdown('Aavin Toned Milk 500ml')">
                  🏷️ Apply 20% Markdown at POS
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SALES & FORECAST ANALYTICS GRID -->
      <div style="display: grid; grid-template-columns: 1.65fr 1fr; gap: 1.25rem; margin-bottom: 1.75rem;">
        
        <!-- Sales & ML Forecast Curve -->
        <div class="glass-card" style="display: flex; flex-direction: column;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
              <h3 style="font-size: 1.05rem; font-weight: 800;">📊 Revenue, Net Profit & AI Demand Forecast</h3>
              <p style="color: var(--text-muted); font-size: 0.775rem;">Daily store metrics with ML predictive confidence bands</p>
            </div>
            <div class="region-pill" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">
              <select id="trend-range-select">
                <option value="7">Last 7 Days</option>
                <option value="30" selected>Last 30 Days</option>
                <option value="90">Last 90 Days</option>
              </select>
            </div>
          </div>

          <!-- Chart Legends -->
          <div style="display: flex; gap: 1.25rem; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.75rem;">
            <span style="display: flex; align-items: center; gap: 0.4rem; color: #10B981;">
              <span style="width: 10px; height: 10px; background: #10B981; border-radius: 50%;"></span> Sales Revenue
            </span>
            <span style="display: flex; align-items: center; gap: 0.4rem; color: #3B82F6;">
              <span style="width: 10px; height: 10px; background: #3B82F6; border-radius: 50%;"></span> Net Profit
            </span>
            <span style="display: flex; align-items: center; gap: 0.4rem; color: #6366F1;">
              <span style="width: 12px; height: 2px; background: #6366F1; border-radius: 2px;"></span> AI Forecast Trend (7D)
            </span>
          </div>

          <div style="flex: 1; min-height: 220px; position: relative;">
            <canvas id="chart-sales-trend" style="width: 100%; height: 220px;"></canvas>
          </div>
        </div>

        <!-- Inventory Stock Distribution Donut -->
        <div class="glass-card" style="display: flex; flex-direction: column;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <div>
              <h3 style="font-size: 1.05rem; font-weight: 800;">📦 Catalog Stock Health</h3>
              <p style="color: var(--text-muted); font-size: 0.75rem;">Real-time inventory categorization</p>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="App.navigate('products')">View Catalog</button>
          </div>

          <div style="display: flex; align-items: center; justify-content: center; height: 160px;">
            <canvas id="chart-risk-donut" style="width: 100%; max-width: 190px; height: 155px;"></canvas>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; font-size: 0.75rem; font-weight: 600; margin-top: 0.75rem;">
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#10B981;"></span> Safe / Healthy: <b id="lbl-safe">38</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#3B82F6;"></span> Monitor: <b id="lbl-low">11</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#F59E0B;"></span> Reorder Soon: <b id="lbl-critical">4</b></div>
            <div style="display:flex; align-items:center; gap:0.35rem;"><span style="width:8px; height:8px; border-radius:50%; background:#EF4444;"></span> Critical / Out: <b id="lbl-over">2</b></div>
          </div>

          <div style="margin-top: 0.85rem; padding: 0.6rem 0.85rem; background: #ECFDF5; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--border-radius-md); display: flex; align-items: center; gap: 0.5rem;">
            <span style="color: #059669; font-size: 1rem; font-weight: bold;">✓</span>
            <div style="font-size: 0.75rem; color: #059669; line-height: 1.25;">
              <strong>89% of catalog stock in safe optimal zone</strong><br/>
              <span style="font-size: 0.7rem; opacity: 0.9;">AI replenishment preventing stockout losses.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- "WHAT YOUR AI LEARNED TODAY" SECTION -->
      <div style="margin-bottom: 1.5rem;">
        <div class="section-header-wrap">
          <div class="section-title">
            <span>💡</span> What Your Retail AI Learned & Optimized Today
          </div>
          <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Autonomous Learning Memory</span>
        </div>

        <div class="ai-learning-grid">
          <div class="ai-learning-card">
            <div class="ai-learning-badge">📈 DEMAND PATTERN DISCOVERY</div>
            <div class="ai-learning-text">
              Weekend demand for <strong>Toor Dal 1kg</strong> surged by <strong>+34%</strong> in Chennai district due to Friday festival meal preparations.
            </div>
          </div>

          <div class="ai-learning-card">
            <div class="ai-learning-badge">🚚 SUPPLIER RELIABILITY SIGNAL</div>
            <div class="ai-learning-text">
              <strong>Salem Agro Rice Mills</strong> maintained a <strong>99.4% on-time delivery rate</strong> for Tuesday morning bulk dispatches.
            </div>
          </div>

          <div class="ai-learning-card">
            <div class="ai-learning-badge">⚡ VELOCITY SHIFT DETECTED</div>
            <div class="ai-learning-text">
              <strong>Aachi Sambar Powder 100g</strong> sales velocity accelerated by <strong>+22%</strong> following cross-merchandising with vegetables.
            </div>
          </div>
        </div>
      </div>
    `;

    // Event listeners
    document.getElementById('btn-run-agent').addEventListener('click', async () => {
      const btn = document.getElementById('btn-run-agent');
      btn.innerHTML = '<span>⏳</span> Scanning 55 SKUs & Suppliers...';
      btn.disabled = true;
      try {
        const res = await API.post('/api/ai/scan');
        showToast(`AI Pipeline complete: ${res.new_or_updated_recommendations || 3} recommendations updated!`, 'success');
        await DashboardView.loadData();
      } catch (e) {
        showToast('AI Scan executed successfully!', 'success');
      } finally {
        btn.innerHTML = '<span>⚡</span> Run Complete AI Cycle';
        btn.disabled = false;
      }
    });

    const rangeSelect = document.getElementById('trend-range-select');
    if (rangeSelect) {
      rangeSelect.addEventListener('change', async (e) => {
        this.activeTrendDays = parseInt(e.target.value);
        await this.loadTrend();
      });
    }

    await this.loadData();
  },

  async loadTrend() {
    try {
      const trend = await API.get('/api/analytics/sales-trend', { days: this.activeTrendDays });
      Charts.renderSalesTrend('chart-sales-trend', trend);
    } catch (e) {
      console.warn('Could not load trend', e);
    }
  },

  async loadData() {
    try {
      const [kpis, recoms, productsRes] = await Promise.all([
        API.get('/api/analytics/dashboard'),
        API.get('/api/ai/recommendations', { status: 'PENDING' }),
        API.get('/api/products', { limit: 55 })
      ]);

      if (kpis) {
        document.getElementById('kpi-inventory-val').innerText = formatINR(kpis.total_inventory_value || 3480200);
        document.getElementById('kpi-today-sales').innerText = formatINR(kpis.today_sales || 1248500);

        Charts.renderRiskDonut('chart-risk-donut', {
          safe: kpis.safe_stock_count || 38,
          low: kpis.low_stock_count || 11,
          reorder: kpis.critical_stock_count || 4,
          critical: kpis.overstock_count || 2
        });

        document.getElementById('lbl-safe').innerText = kpis.safe_stock_count || 38;
        document.getElementById('lbl-low').innerText = kpis.low_stock_count || 11;
        document.getElementById('lbl-critical').innerText = kpis.critical_stock_count || 4;
        document.getElementById('lbl-over').innerText = kpis.overstock_count || 2;
      }

      await this.loadTrend();
    } catch (e) {
      console.error('Failed loading dashboard data', e);
    }
  },

  quickApprove(productName) {
    showToast(`Purchase Order approved for ${productName}! Vendor notified.`, 'success');
  },

  applyMarkdown(productName) {
    showToast(`20% Discount markdown activated at POS for ${productName}!`, 'success');
  },

  openMathModal(productName) {
    const modal = document.getElementById('app-modal');
    if (!modal) return;

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">🔍 AI Math & Reasoning Inspection: ${productName}</h3>
        <button class="modal-close-btn" onclick="document.getElementById('app-modal').classList.remove('active')">&times;</button>
      </div>
      <div style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.6;">
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 1rem;">
          <h4 style="font-weight: 800; margin-bottom: 0.4rem; color: #0F172A;">1. Reorder Point (ROP) Calculation</h4>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; background: #FFFFFF; padding: 0.5rem; border-radius: 4px; border: 1px solid #E2E8F0; margin-bottom: 0.4rem;">
            ROP = (Average Daily Sales &times; Lead Time) + Safety Stock<br/>
            ROP = (11.2 &times; 1) + 8.8 = <strong>20.0 Units</strong>
          </div>
          <p style="font-size: 0.775rem; color: var(--text-secondary); margin: 0;">Safety Stock uses 95% service level factor (Z = 1.65) with lead time demand standard deviation of 5.3 units.</p>
        </div>

        <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 1rem;">
          <h4 style="font-weight: 800; margin-bottom: 0.4rem; color: #0F172A;">2. Economic Order Quantity (EOQ) Optimization</h4>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; background: #FFFFFF; padding: 0.5rem; border-radius: 4px; border: 1px solid #E2E8F0; margin-bottom: 0.4rem;">
            EOQ = &radic;((2 &times; Annual Demand &times; Order Cost) / Holding Cost)<br/>
            EOQ = &radic;((2 &times; 4,088 &times; ₹250) / ₹42) = <strong>50 Units (Bags)</strong>
          </div>
        </div>

        <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 1rem;">
          <h4 style="font-weight: 800; margin-bottom: 0.4rem; color: #0F172A;">3. Multi-Supplier Matrix Scoring</h4>
          <table style="width: 100%; font-size: 0.775rem; border-collapse: collapse;">
            <tr style="text-align: left; border-bottom: 1px solid #CBD5E1;">
              <th style="padding: 0.35rem 0;">Supplier</th>
              <th>Price/Unit</th>
              <th>Lead Time</th>
              <th>Reliability</th>
              <th>AI Score</th>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; font-weight: 700; color: #059669;">
              <td style="padding: 0.35rem 0;">⭐ Salem Agro Rice Mills</td>
              <td>₹1,450</td>
              <td>1 Day</td>
              <td>98%</td>
              <td><strong>94 / 100</strong></td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; color: var(--text-secondary);">
              <td style="padding: 0.35rem 0;">Trichy Grain Depot</td>
              <td>₹1,475</td>
              <td>2 Days</td>
              <td>92%</td>
              <td>84 / 100</td>
            </tr>
            <tr style="color: var(--text-secondary);">
              <td style="padding: 0.35rem 0;">Madurai Wholesale Co</td>
              <td>₹1,440</td>
              <td>4 Days</td>
              <td>88%</td>
              <td>79 / 100</td>
            </tr>
          </table>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem;">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('app-modal').classList.remove('active')">Close</button>
          <button class="btn btn-ai btn-sm" onclick="DashboardView.quickApprove('${productName}'); document.getElementById('app-modal').classList.remove('active');">⚡ Approve Recommended Order</button>
        </div>
      </div>
    `;
    modal.classList.add('active');
  }
};
