// ==============================================================================
// Inventory Management AI: Inventory Ledger & Adjustments Controller
// ==============================================================================

const InventoryView = {
  ledger: [],

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Immutable Inventory Ledger</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Atomic transaction history (Opening + Purchases + Returns - Sales - Damage ± Adjustments)
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <button class="btn btn-secondary" id="btn-record-loss">
            <span>⚠️</span> Record Damage / Expiry
          </button>
          <button class="btn btn-primary" id="btn-manual-adjust">
            <span>⚙️</span> Physical Stock Adjustment
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="glass-card" style="padding: 1rem; margin-bottom: 1.25rem; display: flex; gap: 1rem; align-items: center;">
        <div style="flex: 1;">
          <select id="ledger-type-filter" class="form-control">
            <option value="">All Transaction Types</option>
            <option value="SALE">Sales (Deductions)</option>
            <option value="PURCHASE">Purchases (Inward Stock)</option>
            <option value="CUSTOMER_RETURN">Customer Returns</option>
            <option value="AUDIT_ADJUSTMENT">Audit Adjustments</option>
            <option value="DAMAGE">Damaged Stock</option>
            <option value="EXPIRED">Expired Stock</option>
            <option value="OPENING">Opening Balances</option>
          </select>
        </div>
        <div style="flex: 2;">
          <input type="text" id="ledger-search-input" class="form-control" placeholder="Search by reference ID, reason, or product..." />
        </div>
      </div>

      <!-- Ledger Table -->
      <div class="glass-card" style="padding: 0;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Date & Time</th>
                <th>Product</th>
                <th>Type</th>
                <th>Qty Change</th>
                <th>Balance After</th>
                <th>Reference #</th>
                <th>Recorded By / Reason</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading ledger...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    document.getElementById('ledger-type-filter').addEventListener('change', () => this.loadLedger());
    document.getElementById('btn-manual-adjust').addEventListener('click', () => this.showAdjustmentModal());
    document.getElementById('btn-record-loss').addEventListener('click', () => this.showLossModal());

    await this.loadLedger();
  },

  async loadLedger() {
    const type = document.getElementById('ledger-type-filter')?.value || '';
    try {
      this.ledger = await API.get('/api/inventory/ledger', {
        transaction_type: type,
        limit: 100
      });
      this.renderTable();
    } catch (e) {
      console.error('Failed loading ledger', e);
    }
  },

  renderTable() {
    const tbody = document.getElementById('ledger-table-body');
    if (!tbody) return;

    if (this.ledger.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No transactions found.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.ledger.map(tx => {
      const isPositive = tx.change_qty > 0;
      const typeColors = {
        PURCHASE: 'badge-safe',
        CUSTOMER_RETURN: 'badge-safe',
        SALE: 'badge-monitor',
        AUDIT_ADJUSTMENT: 'badge-warning',
        DAMAGE: 'badge-critical',
        EXPIRED: 'badge-critical',
        OPENING: 'badge-monitor'
      };

      return `
        <tr>
          <td style="font-size: 0.775rem; color: var(--text-secondary); white-space: nowrap;">
            ${tx.created_at ? tx.created_at.substring(0, 16) : '-'}
          </td>
          <td>
            <div style="font-weight: 600;">${tx.product_name}</div>
            <div style="font-size: 0.725rem; color: var(--brand-primary);">${tx.tamil_name || ''}</div>
          </td>
          <td>
            <span class="status-badge ${typeColors[tx.transaction_type] || 'badge-monitor'}">
              ${tx.transaction_type.replace('_', ' ')}
            </span>
          </td>
          <td>
            <span style="font-weight: 700; color: ${isPositive ? 'var(--status-safe)' : 'var(--status-critical)'};">
              ${isPositive ? '+' : ''}${tx.change_qty} ${tx.unit}
            </span>
          </td>
          <td style="font-weight: 700;">
            ${tx.balance_after} ${tx.unit}
          </td>
          <td style="font-family: var(--font-mono); font-size: 0.775rem; color: var(--text-secondary);">
            ${tx.reference_id || '-'}
          </td>
          <td>
            <div style="font-size: 0.8rem;">${tx.reason || '-'}</div>
            <div style="font-size: 0.7rem; color: var(--text-muted);">User: ${tx.user_full_name || tx.username || 'System'}</div>
          </td>
        </tr>
      `;
    }).join('');
  },

  async showAdjustmentModal() {
    const prods = await API.get('/api/products', { limit: 150 });
    const modal = document.getElementById('app-modal');

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">⚙️ Physical Stock Adjustment</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <form id="adjust-form">
        <div class="form-group">
          <label class="form-label">Select Product *</label>
          <select id="adj-product" class="form-control" required>
            ${prods.items.map(p => `<option value="${p.id}" data-current="${p.current_stock}">${p.name} (Current: ${p.current_stock} ${p.unit})</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Verified Physical Count *</label>
          <input type="number" step="0.1" id="adj-physical" class="form-control" placeholder="Enter physical stock found on shelf" required />
        </div>
        <div class="form-group">
          <label class="form-label">Audit Reason / Justification *</label>
          <textarea id="adj-reason" class="form-control" rows="2" placeholder="e.g., Verified in monthly shelf audit section C" required></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Adjustment</button>
        </div>
      </form>
    `;

    App.openModal();
    document.getElementById('adjust-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await API.post('/api/inventory/adjust', {
          product_id: parseInt(document.getElementById('adj-product').value),
          physical_stock: parseFloat(document.getElementById('adj-physical').value),
          reason: document.getElementById('adj-reason').value.trim()
        });
        showToast('Stock adjustment recorded in ledger!', 'success');
        App.closeModal();
        await InventoryView.loadLedger();
      } catch (err) {}
    });
  },

  async showLossModal() {
    const prods = await API.get('/api/products', { limit: 150 });
    const modal = document.getElementById('app-modal');

    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">⚠️ Record Damaged or Expired Stock</h3>
        <button class="modal-close-btn" onclick="App.closeModal()">&times;</button>
      </div>
      <form id="loss-form">
        <div class="form-group">
          <label class="form-label">Select Product *</label>
          <select id="loss-product" class="form-control" required>
            ${prods.items.map(p => `<option value="${p.id}">${p.name} (Current: ${p.current_stock} ${p.unit})</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Type of Loss *</label>
          <select id="loss-type" class="form-control">
            <option value="damage">Damaged Goods / Packaging Spoilage</option>
            <option value="expiry">Expired Stock Deduction</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Quantity to Deduct *</label>
          <input type="number" step="0.1" id="loss-qty" class="form-control" placeholder="Quantity lost" required />
        </div>
        <div class="form-group">
          <label class="form-label">Incident Reason *</label>
          <textarea id="loss-reason" class="form-control" rows="2" placeholder="e.g., Transit bag tear or shelf-life expired" required></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-danger">Deduct Loss</button>
        </div>
      </form>
    `;

    App.openModal();
    document.getElementById('loss-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const isExp = document.getElementById('loss-type').value === 'expiry';
        await API.post('/api/inventory/loss', {
          product_id: parseInt(document.getElementById('loss-product').value),
          quantity: parseFloat(document.getElementById('loss-qty').value),
          is_expired: isExp,
          reason: document.getElementById('loss-reason').value.trim()
        });
        showToast('Loss recorded in immutable ledger.', 'warning');
        App.closeModal();
        await InventoryView.loadLedger();
      } catch (err) {}
    });
  }
};
