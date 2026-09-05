// ==============================================================================
// Inventory Management AI: AI Recommendation Cards & Human Approval Gateway
// ==============================================================================

const AIRecomView = {
  recommendations: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">AI Inventory Replenishment Gateway</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Agentic decision-support engine: Observe → Analyze → Forecast → Reason → Recommend (Human Approval Required)
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <select id="recom-status-filter" class="form-control" style="width: 160px;">
            <option value="PENDING">Pending Approval</option>
            <option value="APPROVED">Approved Orders</option>
            <option value="MODIFIED">Modified Orders</option>
            <option value="REJECTED">Rejected Overrides</option>
            <option value="">All History</option>
          </select>
          <button class="btn btn-primary" id="btn-recom-scan">
            <span>⚡</span> Run Full Agent Scan
          </button>
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
      btn.innerText = 'Scanning...';
      btn.disabled = true;
      try {
        const res = await API.post('/api/ai/scan');
        showToast(`Agent scan finished! ${res.new_or_updated_recommendations} recommendations generated.`, 'success');
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
        <div class="glass-card" style="text-align: center; padding: 3rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
          <h3 style="font-size: 1.15rem; margin-bottom: 0.25rem;">No Pending Actions</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem;">
            All inventory levels are safe or have already been addressed.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.recommendations.map(r => {
      const fb = r.formula_breakdown || {};
      const isPending = r.status === 'PENDING';

      return `
        <div class="recom-card risk-${r.risk_level}">
          <div class="recom-top">
            <div class="recom-title-wrap">
              <div class="recom-prod-name">${r.product_name}</div>
              <div class="recom-tamil-name">${r.tamil_name || ''}</div>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <span class="status-badge badge-${r.risk_level === 'CRITICAL' ? 'critical' : r.risk_level === 'REORDER_NOW' ? 'warning' : 'monitor'}">
                <span class="badge-dot"></span> ${r.risk_level.replace('_', ' ')}
              </span>
              <span class="status-badge" style="background: rgba(255,255,255,0.06); border: 1px solid var(--border-color);">
                ${r.status}
              </span>
            </div>
          </div>

          <!-- Metrics Row -->
          <div class="recom-metrics-row">
            <div class="metric-item">
              <span class="label">Current Stock</span>
              <span class="val" style="color: ${r.current_stock <= 10 ? 'var(--status-critical)' : 'inherit'};">
                ${r.current_stock} ${r.unit}
              </span>
            </div>
            <div class="metric-item">
              <span class="label">Lead Time</span>
              <span class="val">${fb.supplier_lead_time_days || r.supplier_lead_time || 3} days</span>
            </div>
            <div class="metric-item">
              <span class="label">Safety Buffer</span>
              <span class="val">${fb.effective_safety_stock || 10} ${r.unit}</span>
            </div>
            <div class="metric-item">
              <span class="label">Recommended Order</span>
              <span class="val" style="color: var(--brand-primary); font-size: 1.25rem;">
                ${r.recommended_qty} ${r.unit}
              </span>
            </div>
            <div class="metric-item">
              <span class="label">Suggested Supplier</span>
              <span class="val" style="font-size: 0.9rem;">${r.supplier_name || 'Direct Wholesale'}</span>
            </div>
          </div>

          <!-- AI Rationale -->
          <div class="recom-reasoning">
            <strong>🤖 Agent Decision Logic:</strong> ${r.rationale}
          </div>

          <!-- Actions -->
          <div class="recom-actions">
            <button class="btn btn-secondary btn-sm" onclick="AIRecomView.showFormulaModal(${r.id})">
              <span>📐</span> View Math & Formula
            </button>
            ${isPending ? `
              <button class="btn btn-danger btn-sm" onclick="AIRecomView.showRejectModal(${r.id})">
                Reject Override
              </button>
              <button class="btn btn-warning btn-sm" onclick="AIRecomView.showModifyModal(${r.id}, ${r.recommended_qty}, '${r.unit}')">
                Modify Qty
              </button>
              <button class="btn btn-primary btn-sm" onclick="AIRecomView.approve(${r.id})">
                <span>✅</span> Approve Reorder (${r.recommended_qty} ${r.unit})
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
      showToast(`Recommendation approved! Draft Purchase Order #${res.generated_po_number} created automatically.`, 'success');
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
      <div style="padding: 1rem 0;">
        <div class="form-group">
          <label class="form-label">Adjust Order Quantity (${unit})</label>
          <input type="number" id="mod-qty-input" class="form-control" value="${currentQty}" step="1" min="1" required />
          <span style="font-size: 0.725rem; color: var(--text-muted);">
            AI originally recommended ${currentQty} ${unit}. Your adjusted quantity will be ordered.
          </span>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button class="btn btn-primary" id="btn-confirm-modify">Save & Create Purchase Order</button>
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
        showToast(`Quantity modified to ${newQty} ${unit}. Purchase Order #${res.generated_po_number} generated!`, 'success');
        App.closeModal();
        await AIRecomView.loadRecommendations();
      } catch (err) {}
    });
  },

  showRejectModal(recomId) {
    const modal = document.getElementById('app-modal');
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">❌ Reject AI Recommendation</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="padding: 1rem 0;">
        <div class="form-group">
          <label class="form-label">Shopkeeper Override Reason *</label>
          <textarea id="reject-reason-input" class="form-control" rows="3" placeholder="e.g., Seasonal supplier promotion expected next week or slow consumer pickup" required></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button class="btn btn-danger" id="btn-confirm-reject">Reject Recommendation</button>
        </div>
      </div>
    `;

    App.openModal();
    document.getElementById('btn-confirm-reject').addEventListener('click', async () => {
      const reason = document.getElementById('reject-reason-input').value.trim();
      try {
        await API.post(`/api/ai/recommendations/${recomId}/reject`, { reason: reason || 'Shopkeeper manual override' });
        showToast('Recommendation rejected and feedback recorded.', 'warning');
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

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">📐 Transparent Reorder Math & Formula</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">
          ${recom.product_name} (${recom.tamil_name || ''})
        </div>

        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.8;">
          <div><b>1. Current Stock (S):</b> ${fb.current_stock || recom.current_stock} ${recom.unit}</div>
          <div><b>2. Average Daily Sales (ADS):</b> ${fb.average_daily_sales || 0} ${recom.unit}/day</div>
          <div><b>3. Supplier Lead Time (L):</b> ${fb.supplier_lead_time_days || 3} days</div>
          <div><b>4. Lead-Time Demand (LTD = ADS × L):</b> ${fb.lead_time_demand || 0} ${recom.unit}</div>
          <div><b>5. Statistical Safety Stock (SS = Z × σ_D × √L):</b> ${fb.statistical_safety_stock || 10} ${recom.unit}</div>
          <div><b>6. Target Inventory (T = LTD + SS):</b> ${fb.target_inventory || 0} ${recom.unit}</div>
          <div style="border-top: 1px dashed rgba(255,255,255,0.15); margin-top: 0.5rem; padding-top: 0.5rem;">
            <b>7. Raw Reorder Needed (T - S):</b> ${fb.unadjusted_reorder || 0} ${recom.unit}
          </div>
          <div><b>8. Supplier Minimum Order Qty (MOQ):</b> ${fb.supplier_moq || 1} ${recom.unit}</div>
          <div style="font-size: 0.95rem; color: var(--brand-primary); font-weight: bold; margin-top: 0.5rem;">
            FINAL RECOMMENDED ORDER: ${recom.recommended_qty} ${recom.unit}
          </div>
        </div>

        <div style="font-size: 0.825rem; color: var(--text-secondary); line-height: 1.4;">
          <strong>Why this calculation matters:</strong> In Indian retail FMCG and grocery operations, ordering fixed quantities leads to either stockouts during weekend rushes or blocked capital in slow-moving perishables. This transparent formula accounts for both demand volatility and supplier turnaround speed.
        </div>

        <div style="display: flex; justify-content: flex-end; margin-top: 0.5rem;">
          <button class="btn btn-primary btn-sm" onclick="App.closeModal()">Understood</button>
        </div>
      </div>
    `;

    App.openModal();
  }
};
