// ==============================================================================
// Inventory Management AI: Business Reports & Exports Controller
// ==============================================================================

const ReportsView = {
  currentReportType: 'daily_sales',
  reportData: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Retail Business & Audit Reports</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Generate printable GST tax reports, inventory valuations, blocked capital summaries, and scorecards
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <button class="btn btn-secondary" id="btn-print-report">
            <span>🖨️</span> Print / Save PDF
          </button>
          <button class="btn btn-primary" id="btn-export-csv">
            <span>📥</span> Export CSV Data
          </button>
        </div>
      </div>

      <!-- Report Selector Tabs -->
      <div class="glass-card" style="padding: 1rem; margin-bottom: 1.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-secondary btn-sm report-tab active" data-type="daily_sales">Daily Sales</button>
        <button class="btn btn-secondary btn-sm report-tab" data-type="inventory_val">Inventory Valuation</button>
        <button class="btn btn-secondary btn-sm report-tab" data-type="low_stock">Stockout & Low Stock</button>
        <button class="btn btn-secondary btn-sm report-tab" data-type="dead_stock">Dead Stock & Blocked Capital</button>
        <button class="btn btn-secondary btn-sm report-tab" data-type="expiry">FEFO Expiry Risk</button>
        <button class="btn btn-secondary btn-sm report-tab" data-type="suppliers">Supplier Scorecard</button>
      </div>

      <!-- Report Printable Container -->
      <div class="glass-card" id="report-output-card">
        <div id="report-content" style="padding: 1rem;">
          <p style="color: var(--text-muted); text-align: center;">Loading report...</p>
        </div>
      </div>
    `;

    document.querySelectorAll('.report-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentReportType = tab.getAttribute('data-type');
        this.generateReport();
      });
    });

    document.getElementById('btn-print-report').addEventListener('click', () => {
      window.print();
    });

    document.getElementById('btn-export-csv').addEventListener('click', () => {
      this.exportCSV();
    });

    await this.generateReport();
  },

  async generateReport() {
    const container = document.getElementById('report-content');
    if (!container) return;
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center;">Generating ${this.currentReportType} report...</p>`;

    try {
      if (this.currentReportType === 'daily_sales') {
        const sales = await API.get('/api/pos/sales', { limit: 50 });
        this.reportData = sales;
        container.innerHTML = `
          <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem;">
            <h3 style="font-size: 1.25rem;">Daily POS Sales & Tax Summary</h3>
            <p style="color: var(--text-muted); font-size: 0.8rem;">Sri Murugan Super Store - Chennai, Tamil Nadu</p>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Date & Time</th>
                <th>Customer</th>
                <th>Payment Mode</th>
                <th>Base Value</th>
                <th>GST Amount</th>
                <th>Grand Total</th>
              </tr>
            </thead>
            <tbody>
              ${sales.map(s => `
                <tr>
                  <td style="font-family: var(--font-mono); font-weight: bold;">${s.invoice_number}</td>
                  <td>${s.created_at ? s.created_at.substring(0, 16) : '-'}</td>
                  <td>${s.customer_name}</td>
                  <td><span class="status-badge badge-monitor">${s.payment_method}</span></td>
                  <td>${formatINR(s.subtotal)}</td>
                  <td>${formatINR(s.gst_amount)}</td>
                  <td style="font-weight: 700; color: var(--brand-primary);">${formatINR(s.total_amount)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else if (this.currentReportType === 'inventory_val') {
        const prods = await API.get('/api/products', { limit: 200 });
        this.reportData = prods.items;
        const totalVal = prods.items.reduce((acc, p) => acc + (p.inventory_value || 0), 0);
        container.innerHTML = `
          <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
              <h3 style="font-size: 1.25rem;">Comprehensive Inventory Valuation Report</h3>
              <p style="color: var(--text-muted); font-size: 0.8rem;">Itemized asset value based on wholesale purchase cost</p>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 0.8rem; color: var(--text-muted);">Total Inventory Value:</span>
              <div style="font-size: 1.5rem; font-weight: 800; color: var(--brand-primary);">${formatINR(totalVal)}</div>
            </div>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Stock Qty</th>
                <th>Purchase Cost</th>
                <th>Selling Price</th>
                <th>GST Rate</th>
                <th>Total Valuation (₹)</th>
              </tr>
            </thead>
            <tbody>
              ${prods.items.map(p => `
                <tr>
                  <td>
                    <div style="font-weight: 700;">${p.name}</div>
                    <div style="font-size: 0.725rem; color: var(--brand-primary);">${p.tamil_name || ''}</div>
                  </td>
                  <td>${p.category_name}</td>
                  <td style="font-weight: 700;">${p.current_stock} ${p.unit}</td>
                  <td>${formatINR(p.purchase_price)}</td>
                  <td>${formatINR(p.selling_price)}</td>
                  <td>${p.gst_rate}%</td>
                  <td style="font-weight: 700;">${formatINR(p.inventory_value)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else if (this.currentReportType === 'dead_stock') {
        const dead = await API.get('/api/ai/dead-stock');
        this.reportData = dead;
        const totalBlocked = dead.reduce((acc, it) => acc + it.blocked_capital, 0);
        container.innerHTML = `
          <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
              <h3 style="font-size: 1.25rem;">Dead Stock & Blocked Working Capital Report</h3>
              <p style="color: var(--text-muted); font-size: 0.8rem;">Products with zero/negligible sales tying up store liquidity</p>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 0.8rem; color: var(--text-muted);">Total Blocked Capital:</span>
              <div style="font-size: 1.5rem; font-weight: 800; color: var(--status-critical);">${formatINR(totalBlocked)}</div>
            </div>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Stock Idle</th>
                <th>Days Since Sale</th>
                <th>Blocked Capital (₹)</th>
                <th>Classification</th>
                <th>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              ${dead.map(d => `
                <tr>
                  <td>
                    <div style="font-weight: 700;">${d.product_name}</div>
                    <div style="font-size: 0.725rem; color: var(--brand-primary);">${d.tamil_name || ''}</div>
                  </td>
                  <td>${d.current_stock} ${d.unit}</td>
                  <td>${d.days_idle} days</td>
                  <td style="font-weight: 700; color: var(--status-critical);">${formatINR(d.blocked_capital)}</td>
                  <td><span class="status-badge badge-warning">${d.classification}</span></td>
                  <td>${d.recommended_action}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else if (this.currentReportType === 'expiry') {
        const exp = await API.get('/api/ai/expiry');
        this.reportData = exp;
        container.innerHTML = `
          <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem;">
            <h3 style="font-size: 1.25rem;">FEFO Shelf-Life Expiry Risk Report</h3>
            <p style="color: var(--text-muted); font-size: 0.8rem;">Batch expiration timelines and projected loss</p>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Batch #</th>
                <th>Product</th>
                <th>Expiry Date</th>
                <th>Days Left</th>
                <th>Batch Stock</th>
                <th>Projected Unsold Loss</th>
              </tr>
            </thead>
            <tbody>
              ${exp.map(b => `
                <tr>
                  <td style="font-family: var(--font-mono); font-weight: bold;">${b.batch_number}</td>
                  <td>${b.product_name}</td>
                  <td>${b.expiry_date}</td>
                  <td style="font-weight: bold; color: var(--status-critical);">${b.days_to_expiry} days</td>
                  <td>${b.remaining_qty} ${b.unit}</td>
                  <td style="font-weight: bold; color: var(--status-critical);">${formatINR(b.potential_loss_inr)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      } else {
        container.innerHTML = `<p style="text-align: center; color: var(--text-muted);">Select a report above to generate view.</p>`;
      }
    } catch (e) {
      console.error('Report error', e);
    }
  },

  exportCSV() {
    if (!this.reportData || this.reportData.length === 0) {
      showToast('No data available to export', 'warning');
      return;
    }
    const headers = Object.keys(this.reportData[0]);
    const csvRows = [headers.join(',')];
    this.reportData.forEach(row => {
      const values = headers.map(h => {
        const val = row[h];
        return typeof val === 'string' ? `"${val.replace(/"/g, '""')}"` : val;
      });
      csvRows.push(values.join(','));
    });
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', `${this.currentReportType}_report_${new Date().toISOString().substring(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast('CSV downloaded successfully!', 'success');
  }
};
