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
          <h2 style="font-size: 1.4rem;">Physical Stock Audits & Discrepancies</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Physical shelf verification, automated variance detection, and neutral AI cause investigation
          </p>
        </div>
        <button class="btn btn-primary" id="btn-start-audit">
          <span>📋</span> Start New Audit Session
        </button>
      </div>

      <!-- Active / Recent Audits Grid -->
      <div class="glass-card" style="margin-bottom: 1.5rem; padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Audit Number</th>
                <th>Date Initiated</th>
                <th>Conducted By</th>
                <th>Items Verified</th>
                <th>Discrepancies Found</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="audits-list-body">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading audits...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Audit Items Details Panel -->
      <div class="glass-card" id="audit-details-card" style="display: none;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <div>
            <h3 style="font-size: 1.1rem;" id="audit-detail-title">Audit Items & Diagnostics</h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Discrepancy cause investigation and atomic ledger reconciliation</p>
          </div>
          <button class="btn btn-primary btn-sm" id="btn-reconcile-audit">
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
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">No stock audits conducted yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = this.audits.map(a => `
        <tr>
          <td><strong style="font-family: var(--font-mono);">${a.audit_number}</strong></td>
          <td>${a.audit_date ? a.audit_date.substring(0, 16) : '-'}</td>
          <td>${a.conducted_by_name || 'Store Manager'}</td>
          <td>${a.total_items_checked || 0}</td>
          <td>
            <span style="font-weight: 700; color: ${a.discrepancy_count > 0 ? 'var(--status-critical)' : 'var(--status-safe)'};">
              ${a.discrepancy_count} item(s)
            </span>
          </td>
          <td>
            <span class="status-badge badge-${a.status === 'COMPLETED' ? 'safe' : 'warning'}">
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

      // Auto-open first audit details if available
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
      title.innerText = `Audit Items: ${this.currentAudit.audit_number} (${this.currentAudit.status})`;

      reconcileBtn.style.display = this.currentAudit.status === 'COMPLETED' ? 'none' : 'inline-flex';
      reconcileBtn.onclick = () => this.reconcile(this.currentAudit.id);

      const items = this.currentAudit.items || [];
      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No counted items in this audit.</td></tr>`;
        return;
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
              <span style="font-weight: 800; color: ${hasVariance ? (it.variance_qty < 0 ? 'var(--status-critical)' : 'var(--accent-saffron)') : 'var(--status-safe)'};">
                ${it.variance_qty > 0 ? '+' : ''}${it.variance_qty} ${it.unit}
              </span>
            </td>
            <td>
              <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.35; max-width: 380px;">
                ${it.ai_likely_cause || 'Stock matched perfectly.'}
              </div>
            </td>
            <td>
              <span class="status-badge badge-${it.action_taken === 'RECONCILED' ? 'safe' : 'warning'}">
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
      showToast(`Reconciled ${res.items_reconciled} discrepancy items into the ledger! Audit marked COMPLETED.`, 'success');
      await this.loadAudits();
      await this.viewAuditDetails(auditId);
    } catch (e) {}
  }
};
