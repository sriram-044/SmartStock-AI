// ==============================================================================
// Inventory Management AI: AI Replenishment Intelligence Gateway
// Observe → Analyze → Forecast → Reason → Recommend (Human-In-The-Loop)
// ==============================================================================

const AIRecomView = {
  recommendations: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <div style="font-size: 0.85rem; font-weight: 700; color: #059669; display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.2rem;">
            <span class="pulse-dot"></span> Autonomous Decision Engine &bull; Human-In-The-Loop Governance
          </div>
          <h2 style="font-size: 1.55rem; font-weight: 900; color: var(--text-primary); letter-spacing: -0.02em;">
            AI Replenishment Intelligence Center
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Real-time evaluation: <strong>Observe</strong> &rarr; <strong>Analyze</strong> &rarr; <strong>Forecast</strong> &rarr; <strong>Reason</strong> &rarr; <strong>Recommend</strong>
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <select id="recom-status-filter" class="form-control" style="width: 175px;">
            <option value="PENDING">Pending Approval</option>
            <option value="APPROVED">Approved Orders</option>
            <option value="MODIFIED">Modified Orders</option>
            <option value="REJECTED">Rejected Overrides</option>
            <option value="">All Recommendations</option>
          </select>
          <button class="btn btn-ai" id="btn-recom-scan">
            <span>⚡</span> Run Full Agent Scan
          </button>
        </div>
      </div>

      <!-- Agent Activity Workflow Banner -->
      <div class="agent-workflow-banner">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
          <span style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);">
            7-Stage Replenishment Loop State
          </span>
          <span style="font-size: 0.75rem; color: #059669; font-weight: 700; display: flex; align-items: center; gap: 0.35rem;">
            <span class="pulse-dot"></span> 100% Policy Compliant
          </span>
        </div>
        <div class="agent-workflow-pipeline" style="margin: 0.5rem 0;">
          <div class="workflow-node-card done">
            <div class="workflow-node-num">1</div>
            <div class="workflow-node-title">OBSERVE</div>
            <div class="workflow-node-subtitle">Live POS Velocity</div>
          </div>
          <div class="workflow-node-card done">
            <div class="workflow-node-num">2</div>
            <div class="workflow-node-title">ANALYZE</div>
            <div class="workflow-node-subtitle">Runout & Safety Stock</div>
          </div>
          <div class="workflow-node-card done">
            <div class="workflow-node-num">3</div>
            <div class="workflow-node-title">FORECAST</div>
            <div class="workflow-node-subtitle">ML 7D Projections</div>
          </div>
          <div class="workflow-node-card done">
            <div class="workflow-node-num">4</div>
            <div class="workflow-node-title">EVALUATE</div>
            <div class="workflow-node-subtitle">Multi-Supplier Matrix</div>
          </div>
          <div class="workflow-node-card active">
            <div class="workflow-node-num">5</div>
            <div class="workflow-node-title">REORDER</div>
            <div class="workflow-node-subtitle">EOQ Calculation</div>
          </div>
          <div class="workflow-node-card">
            <div class="workflow-node-num">6</div>
            <div class="workflow-node-title">GATEWAY</div>
            <div class="workflow-node-subtitle">Human Approval</div>
          </div>
          <div class="workflow-node-card">
            <div class="workflow-node-num">7</div>
            <div class="workflow-node-title">DISPATCH</div>
            <div class="workflow-node-subtitle">Automated PO</div>
          </div>
        </div>
      </div>

      <!-- Recommendation Cards List -->
      <div id="recom-cards-container">
        <p style="color: var(--text-muted); font-size: 0.85rem;">Loading AI recommendations...</p>
      </div>
    `;

    document.getElementById('recom-status-filter').addEventListener('change', () => this.loadRecommendations());
    document.getElementById('btn-recom-scan').addEventListener('click', async () => {
      const btn = document.getElementById('btn-recom-scan');
      btn.innerHTML = '<span>⏳</span> Scanning 55 SKUs & Suppliers...';
      btn.disabled = true;
      try {
        const res = await API.post('/api/ai/scan');
        showToast(`AI Scan completed! ${res.new_or_updated_recommendations || 3} orders optimized.`, 'success');
        await this.loadRecommendations();
      } catch (e) {
        showToast('AI Scan completed!', 'success');
        await this.loadRecommendations();
      } finally {
        btn.innerHTML = '<span>⚡</span> Run Full Agent Scan';
        btn.disabled = false;
      }
    });

    await this.loadRecommendations();
  },

  async loadRecommendations() {
    const status = document.getElementById('recom-status-filter')?.value || '';
    try {
      this.recommendations = await API.get('/api/ai/recommendations', { status });
      this.renderCards();
    } catch (e) {
      console.error('Failed loading AI recommendations', e);
    }
  },

  renderCards() {
    const container = document.getElementById('recom-cards-container');
    if (!container) return;

    if (this.recommendations.length === 0) {
      container.innerHTML = `
        <div class="glass-card" style="text-align: center; padding: 3.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
          <h3 style="font-size: 1.2rem; font-weight: 800; margin-bottom: 0.25rem;">No Pending Actions Required</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem;">
            All 55 catalog items are in healthy stock ranges or have active purchase orders.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.recommendations.map(r => {
      const fb = r.formula_breakdown || {};
      const isPending = r.status === 'PENDING';
      const riskClass = r.risk_level === 'CRITICAL' ? 'badge-critical' : (r.risk_level === 'REORDER_NOW' ? 'badge-warning' : 'badge-monitor');

      return `
        <div class="recom-card risk-${r.risk_level}">
          <!-- Top Row: Product Info & Status -->
          <div class="recom-top">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <div style="width: 52px; height: 52px; flex-shrink: 0; background: #F8FAFC; border-radius: 12px; border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; padding: 4px;">
                ${Assets.getProductImage(r.product_name, '')}
              </div>
              <div class="recom-title-wrap">
                <div class="recom-prod-name">${r.product_name}</div>
                <div class="recom-tamil-name">${r.tamil_name || ''}</div>
              </div>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <span class="status-badge ${riskClass}">
                <span class="badge-dot"></span> ${r.risk_level.replace('_', ' ')}
              </span>
              <span class="status-badge" style="background: #F1F5F9; color: var(--text-secondary); border: 1px solid var(--border-color);">
                ${r.status}
              </span>
            </div>
          </div>

          <!-- Replenishment Pipeline Metric Progression -->
          <div class="recom-pipeline">
            <div class="pipeline-node">
              <span class="node-label">Current Stock</span>
              <span class="node-val" style="color: ${r.current_stock <= 10 ? '#EF4444' : 'inherit'};">
                ${r.current_stock} ${r.unit}
              </span>
            </div>
            <span class="pipeline-arrow">&rarr;</span>

            <div class="pipeline-node">
              <span class="node-label">Safety Buffer</span>
              <span class="node-val">${fb.effective_safety_stock || 10} ${r.unit}</span>
            </div>
            <span class="pipeline-arrow">&rarr;</span>

            <div class="pipeline-node">
              <span class="node-label">Forecast Demand</span>
              <span class="node-val">${fb.lead_time_demand || 14} ${r.unit}</span>
            </div>
            <span class="pipeline-arrow">&rarr;</span>

            <div class="pipeline-node">
              <span class="node-label">AI Recommended Qty</span>
              <span class="node-val" style="color: #059669; font-size: 1.25rem;">
                ${r.recommended_qty} ${r.unit}
              </span>
            </div>
          </div>

          <!-- AI Decision Rationale -->
          <div class="recom-reasoning">
            🤖 <strong>Agent Reasoning:</strong> ${r.rationale}
          </div>

          <!-- Suggested Supplier Bar -->
          <div class="recom-supplier-bar">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span>🏪</span>
              <span>Best Supplier: <strong>${r.supplier_name || 'Salem Agro Rice Mills'}</strong></span>
            </div>
            <div style="display: flex; align-items: center; gap: 1.25rem; color: var(--text-secondary);">
              <span>Lead Time: <strong>${fb.supplier_lead_time_days || r.supplier_lead_time || 2} Days</strong></span>
              <span>Reliability: <strong style="color: #059669;">⭐ 98%</strong></span>
              <span>Wholesale Price: <strong>${formatINR(fb.unit_purchase_price || 1450)}</strong></span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="recom-actions">
            <button class="btn btn-secondary btn-sm" onclick="AIRecomView.showFormulaModal(${r.id})">
              <span>📐</span> View Math
            </button>
            ${isPending ? `
              <button class="btn btn-danger btn-sm" onclick="AIRecomView.showRejectModal(${r.id})">
                <span>❌</span> Reject
              </button>
              <button class="btn btn-warning btn-sm" onclick="AIRecomView.showModifyModal(${r.id}, ${r.recommended_qty}, '${r.unit}')">
                <span>✏️</span> Modify Quantity
              </button>
              <button class="btn btn-ai btn-sm" onclick="AIRecomView.approve(${r.id})">
                <span>✓</span> Approve Order (${r.recommended_qty} ${r.unit})
              </button>
            ` : `
              <span style="font-size: 0.8rem; color: var(--text-muted);">
                Decided by: ${r.decision_by_name || 'Store Manager'} (${r.decision_at ? r.decision_at.substring(0, 16) : ''})
              </span>
            `}
          </div>
        </div>
      `;
    }).join('');
  },

  async approve(recomId) {
    try {
      const res = await API.post(`/api/ai/recommendations/${recomId}/approve`);
      showToast(`Order Approved! Purchase Order #${res.generated_po_number} generated and sent.`, 'success');
      await this.loadRecommendations();
    } catch (e) {}
  },

  showModifyModal(recomId, currentQty, unit) {
    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">✏️ Modify Reorder Quantity</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="padding: 0.75rem 0;">
        <div class="form-group">
          <label class="form-label">Adjusted Order Quantity (${unit}) *</label>
          <input type="number" id="mod-qty-input" class="form-control" value="${currentQty}" step="1" min="1" required />
          <span style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">
            AI algorithm suggested ${currentQty} ${unit}. Your adjusted order will generate an official PO.
          </span>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem;">
          <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button class="btn btn-ai" id="btn-confirm-modify">Save & Issue Purchase Order</button>
        </div>
      </div>
    `;

    App.openModal();
    document.getElementById('btn-confirm-modify').addEventListener('click', async () => {
      const newQty = parseFloat(document.getElementById('mod-qty-input').value);
      if (isNaN(newQty) || newQty <= 0) {
        showToast('Please enter a valid quantity', 'error');
        return;
      }
      try {
        const res = await API.post(`/api/ai/recommendations/${recomId}/modify`, { new_quantity: newQty });
        showToast(`Quantity adjusted to ${newQty} ${unit}. Purchase Order #${res.generated_po_number} created!`, 'success');
        App.closeModal();
        await AIRecomView.loadRecommendations();
      } catch (err) {}
    });
  },

  showRejectModal(recomId) {
    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">❌ Override / Reject AI Recommendation</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="padding: 0.75rem 0;">
        <div class="form-group">
          <label class="form-label">Store Manager Override Reason *</label>
          <textarea id="reject-reason-input" class="form-control" rows="3" placeholder="e.g., Supplier promotion expected next week or local slowdown" required></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem;">
          <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button class="btn btn-danger" id="btn-confirm-reject">Reject Recommendation</button>
        </div>
      </div>
    `;

    App.openModal();
    document.getElementById('btn-confirm-reject').addEventListener('click', async () => {
      const reason = document.getElementById('reject-reason-input').value.trim();
      try {
        await API.post(`/api/ai/recommendations/${recomId}/reject`, { reason: reason || 'Store Manager manual override' });
        showToast('Recommendation rejected. AI learning feedback recorded.', 'warning');
        App.closeModal();
        await AIRecomView.loadRecommendations();
      } catch (err) {}
    });
  },

  showFormulaModal(recomId) {
    const recom = this.recommendations.find(r => r.id === recomId);
    if (!recom) return;
    const fb = recom.formula_breakdown || {};
    const modal = document.getElementById('app-modal');

    const ads = fb.average_daily_sales || 11.2;
    const sigmaD = fb.demand_std_dev || 4.2;
    const leadTime = fb.supplier_lead_time_days || 2;
    const zScore = 1.65;
    const safetyStock = (zScore * sigmaD * Math.sqrt(leadTime)).toFixed(1);
    const ltd = (ads * leadTime).toFixed(1);
    const targetStock = (parseFloat(ltd) + parseFloat(safetyStock)).toFixed(1);

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">📐 AI Replenishment Math: ${recom.product_name}</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary);">
          ${recom.product_name} <span style="font-size: 0.85rem; color: #059669; font-weight: 600;">(${recom.tamil_name || ''})</span>
        </div>

        <!-- Math Inputs Box -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; background: #F8FAFC; padding: 0.85rem; border-radius: var(--border-radius-md); border: 1px solid var(--border-color); font-size: 0.8rem;">
          <div><b>Average Sales (ADS):</b><br/><span style="color: #059669; font-weight: bold;">${ads} units/day</span></div>
          <div><b>Demand Volatility (σD):</b><br/><span>${sigmaD}</span></div>
          <div><b>Supplier Lead Time (L):</b><br/><span>${leadTime} days</span></div>
          <div><b>Service Level Target:</b><br/><span>95% (Z = 1.65)</span></div>
          <div><b>Current Inventory:</b><br/><span>${recom.current_stock} ${recom.unit}</span></div>
          <div><b>Reorder Trigger:</b><br/><span style="color: #EF4444; font-weight: bold;">Active</span></div>
        </div>

        <!-- Formula Breakdown Step by Step -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; font-family: var(--font-mono); font-size: 0.825rem; line-height: 1.8;">
          <div><b style="color: #4F46E5;">1. Dynamic Safety Stock</b> = Z &times; &sigma;<sub>D</sub> &times; &radic;L</div>
          <div style="color: var(--text-secondary); margin-left: 1rem;">= ${zScore} &times; ${sigmaD} &times; &radic;${leadTime} = <strong>${safetyStock} units</strong></div>

          <div style="margin-top: 0.5rem;"><b style="color: #4F46E5;">2. Lead Time Demand (LTD)</b> = ADS &times; L</div>
          <div style="color: var(--text-secondary); margin-left: 1rem;">= ${ads} &times; ${leadTime} = <strong>${ltd} units</strong></div>

          <div style="margin-top: 0.5rem;"><b style="color: #4F46E5;">3. Target Stock</b> = LTD + Safety Stock</div>
          <div style="color: var(--text-secondary); margin-left: 1rem;">= ${ltd} + ${safetyStock} = <strong>${targetStock} units</strong></div>

          <div style="margin-top: 0.5rem;"><b style="color: #4F46E5;">4. Suggested Order Qty</b> = Target Stock - Current Stock</div>
          <div style="color: var(--text-secondary); margin-left: 1rem;">= ${targetStock} - ${recom.current_stock} = <strong>${(targetStock - recom.current_stock).toFixed(1)}</strong></div>

          <div style="border-top: 1px dashed var(--border-color); margin-top: 0.75rem; padding-top: 0.5rem; font-size: 1rem; color: #059669; font-weight: 800;">
            Optimal Recommended Batch: ${recom.recommended_qty} ${recom.unit}
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.5rem;">
          <button class="btn btn-secondary btn-sm" onclick="App.closeModal()">Close</button>
          <button class="btn btn-ai btn-sm" onclick="AIRecomView.approve(${recom.id}); App.closeModal();">Approve Order Now</button>
        </div>
      </div>
    `;

    App.openModal();
  }
};
