// ==============================================================================
// Inventory Management AI: Stock Audits & Discrepancy Diagnostics Controller
// ==============================================================================

const AuditsView = {
  audits: [],
  currentAudit: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem; font-weight: 900; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>🔍</span> Physical Stock Audits & Diagnostics
          </h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Physical shelf verification, automated variance detection, and neutral AI root-cause diagnostics
          </p>
        </div>
        <button class="btn btn-primary" id="btn-start-audit">
          <span>📋</span> Start New Audit Session
        </button>
      </div>

      <!-- Audit Progress Card -->
      <div class="glass-card" style="margin-bottom: 1.5rem; padding: 1.25rem 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <div style="font-size: 0.85rem; font-weight: 800; color: var(--text-primary);">Audit Verification Progress</div>
          <div style="font-size: 0.85rem; font-weight: 800; color: var(--brand-primary);" id="audit-progress-text">Verified 12 / 25 items</div>
        </div>
        <div style="height: 8px; background: #E5E7EB; border-radius: 9999px; overflow: hidden;">
          <div id="audit-progress-bar" style="height: 100%; width: 48%; background: var(--gradient-ai-red);"></div>
        </div>
      </div>

      <!-- Active / Recent Audits List -->
      <div class="glass-card" style="margin-bottom: 1.5rem; padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Audit Number</th>
                <th>Date Initiated</th>
                <th>Conducted By</th>
                <th>Items Verified</th>
                <th>Discrepancies</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="audits-list-body">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Loading audits...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Audit Items Details Panel -->
      <div class="glass-card" id="audit-details-card" style="display: none;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
          <div>
            <h3 style="font-size: 1.1rem; font-weight: 800;" id="audit-detail-title">Audit Items & AI Diagnostics</h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Discrepancy cause investigation and atomic ledger reconciliation</p>
          </div>
          <button class="btn btn-success btn-sm" id="btn-reconcile-audit">
            <span>⚖️</span> One-Click Reconcile Discrepancies
          </button>
        </div>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>System Stock</th>
                <th>Physical Count</th>
                <th>Variance</th>
                <th>AI Diagnostic (Likely Cause)</th>
                <th>Action Status</th>
              </tr>
            </thead>
            <tbody id="audit-items-body"></tbody>
          </table>
        </div>
      </div>
    `;

    document.getElementById('btn-start-audit').addEventListener('click', () => this.startNewAudit());
    await this.loadAudits();
  },

  async loadAudits() {
    try {
      this.audits = await API.get('/api/audits');
      const tbody = document.getElementById('audits-list-body');
      if (!tbody) return;

      if (this.audits.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">No stock audits conducted yet. Click "Start New Audit Session" to begin.</td></tr>`;
        return;
      }

      tbody.innerHTML = this.audits.map(a => `
        <tr>
          <td><strong style="font-family: var(--font-mono);">${a.audit_number}</strong></td>
          <td>${a.audit_date ? a.audit_date.substring(0, 16) : '-'}</td>
          <td>${a.conducted_by_name || 'Store Manager'}</td>
          <td><strong>${a.total_items_checked || 0}</strong></td>
          <td>
            <span style="font-weight: 800; color: ${a.discrepancy_count > 0 ? '#DC2626' : '#16A34A'};">
              ${a.discrepancy_count} item(s)
            </span>
          </td>
          <td>
            <span class="status-badge ${a.status === 'COMPLETED' ? 'badge-safe' : 'badge-warning'}">
              ${a.status}
            </span>
          </td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="AuditsView.viewAuditDetails(${a.id})">
              Inspect Variances
            </button>
          </td>
        </tr>
      `).join('');

      if (this.audits.length > 0) {
        this.viewAuditDetails(this.audits[0].id);
      }
    } catch (e) {
      console.error('Failed loading audits', e);
    }
  },

  async viewAuditDetails(auditId) {
    try {
      this.currentAudit = await API.get(`/api/audits/${auditId}`);
      const panel = document.getElementById('audit-details-card');
      const tbody = document.getElementById('audit-items-body');
      const title = document.getElementById('audit-detail-title');
      const reconcileBtn = document.getElementById('btn-reconcile-audit');

      if (!panel || !tbody) return;
      panel.style.display = 'block';
      title.innerText = `Audit Session: ${this.currentAudit.audit_number} (${this.currentAudit.status})`;

      reconcileBtn.style.display = this.currentAudit.status === 'COMPLETED' ? 'none' : 'inline-flex';
      reconcileBtn.onclick = () => this.reconcile(this.currentAudit.id);

      const items = this.currentAudit.items || [];
      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No counted items in this audit session.</td></tr>`;
        return;
      }

      // Update progress bar
      const progressText = document.getElementById('audit-progress-text');
      const progressBar = document.getElementById('audit-progress-bar');
      if (progressText && progressBar) {
        progressText.innerText = `Verified ${items.length} items in Session ${this.currentAudit.audit_number}`;
        progressBar.style.width = this.currentAudit.status === 'COMPLETED' ? '100%' : '75%';
      }

      tbody.innerHTML = items.map(it => {
        const hasVariance = Math.abs(it.variance_qty) > 0.001;
        return `
          <tr>
            <td>
              <div style="font-weight: 700;">${it.product_name}</div>
              <div style="font-size: 0.725rem; color: var(--brand-primary);">${it.tamil_name || ''}</div>
            </td>
            <td>${it.system_stock} ${it.unit}</td>
            <td style="font-weight: 700;">${it.physical_stock} ${it.unit}</td>
            <td>
              <span style="font-weight: 800; font-size: 0.95rem; color: ${hasVariance ? (it.variance_qty < 0 ? '#DC2626' : '#D97706') : '#16A34A'};">
                ${it.variance_qty > 0 ? '+' : ''}${it.variance_qty} ${it.unit}
              </span>
            </td>
            <td>
              <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4; max-width: 380px;">
                💡 ${it.ai_likely_cause || 'Physical stock matches ledger recorded balance.'}
              </div>
            </td>
            <td>
              <span class="status-badge ${it.action_taken === 'RECONCILED' ? 'badge-safe' : 'badge-warning'}">
                ${it.action_taken || 'PENDING'}
              </span>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error('Failed viewing audit details', e);
    }
  },

  async startNewAudit() {
    try {
      const res = await API.post('/api/audits/start', { notes: 'Physical Stock Verification' });
      showToast(`Audit Session ${res.audit_number} started!`, 'success');
      await this.loadAudits();
    } catch (e) {}
  },

  async reconcile(auditId) {
    try {
      const res = await API.post(`/api/audits/${auditId}/reconcile`);
      showToast(`Reconciled ${res.items_reconciled} discrepancy items into ledger! Audit completed.`, 'success');
      await this.loadAudits();
      await this.viewAuditDetails(auditId);
    } catch (e) {}
  }
};
