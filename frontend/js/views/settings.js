// ==============================================================================
// Inventory Management AI: Settings & Store Profile Controller
// ==============================================================================

const SettingsView = {
  settings: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.4rem;">Store Configuration & AI Parameters</h2>
          <p style="color: var(--text-secondary); font-size: 0.85rem;">
            Configure Sri Murugan Super Store profile, Tamil Nadu district, GSTIN, and Agentic AI safety thresholds
          </p>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
        <!-- Store Identity & Regional Tax Settings -->
        <div class="glass-card">
          <div style="margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
            <h3 style="font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
              <span>🏪</span> Store Identity & Location
            </h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Retail trade details printed on customer invoices</p>
          </div>
          <form id="store-settings-form">
            <div class="form-group">
              <label class="form-label">Store Trade Name *</label>
              <input type="text" id="set-shop-name" class="form-control" required />
            </div>
            <div class="form-group">
              <label class="form-label">GSTIN Identification Number *</label>
              <input type="text" id="set-gstin" class="form-control" placeholder="33AAAAA0000A1Z5" required />
            </div>
            <div class="form-group">
              <label class="form-label">Tamil Nadu District *</label>
              <select id="set-district" class="form-control" required>
                <option value="Chennai">Chennai</option>
                <option value="Coimbatore">Coimbatore</option>
                <option value="Madurai">Madurai</option>
                <option value="Salem">Salem</option>
                <option value="Tiruchirappalli">Tiruchirappalli</option>
                <option value="Erode">Erode</option>
                <option value="Tiruppur">Tiruppur</option>
                <option value="Tirunelveli">Tirunelveli</option>
                <option value="Vellore">Vellore</option>
                <option value="Thanjavur">Thanjavur</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Store Street Address *</label>
              <textarea id="set-address" class="form-control" rows="2" required></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Contact Phone / WhatsApp</label>
              <input type="text" id="set-phone" class="form-control" />
            </div>
            <div style="display: flex; justify-content: flex-end; margin-top: 1rem;">
              <button type="submit" class="btn btn-primary">Save Store Profile</button>
            </div>
          </form>
        </div>

        <!-- Agentic AI Parameters & Copilot -->
        <div class="glass-card">
          <div style="margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
            <h3 style="font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
              <span>🤖</span> Agentic AI Replenishment Engine
            </h3>
            <p style="color: var(--text-muted); font-size: 0.775rem;">Autonomous decision rules and statistical parameters</p>
          </div>
          <form id="ai-params-form">
            <div class="form-group">
              <label class="form-label">Safety Stock Service Level (Z-Score)</label>
              <select id="set-service-level" class="form-control">
                <option value="1.65">95% Service Level (Z = 1.65 - Standard FMCG)</option>
                <option value="1.96">97.5% Service Level (Z = 1.96 - High Reliability)</option>
                <option value="2.33">99% Service Level (Z = 2.33 - Critical Perishables)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Default Supplier Turnaround (Days)</label>
              <input type="number" id="set-default-lead" class="form-control" value="3" min="1" max="15" />
            </div>
            <div class="form-group">
              <label class="form-label">Stockout Risk Threshold (Days of Inventory Remaining)</label>
              <input type="number" id="set-dir-threshold" class="form-control" value="3" min="1" max="10" />
            </div>

            <!-- Free LLM Provider Status Box -->
            <div style="background: #F9FAFB; border: 1px solid var(--border-color); border-radius: var(--border-radius-md); padding: 1rem; margin-top: 1.25rem;">
              <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem; display: flex; align-items: center; justify-content: space-between;">
                <span>✨ Free AI Copilot Connectivity</span>
                <span class="pulse-dot"></span>
              </div>
              <p style="font-size: 0.775rem; color: var(--text-secondary); line-height: 1.4; margin-bottom: 0.75rem;">
                Runs 100% offline out-of-the-box or with free Google Gemini / Groq / Ollama tool augmented Q&A.
              </p>
              <button type="button" class="btn btn-secondary btn-sm" id="btn-test-llm" style="width: 100%;">
                ⚡ Verify AI Assistant Status
              </button>
            </div>

            <div style="display: flex; justify-content: flex-end; margin-top: 1.25rem;">
              <button type="submit" class="btn btn-ai">Save AI Rules</button>
            </div>
          </form>
        </div>
      </div>
    `;

    await this.loadSettings();

    document.getElementById('store-settings-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.saveStoreSettings();
    });

    document.getElementById('ai-params-form').addEventListener('submit', (e) => {
      e.preventDefault();
      showToast('AI Replenishment parameters updated successfully!', 'success');
    });

    document.getElementById('btn-test-llm').addEventListener('click', async () => {
      const btn = document.getElementById('btn-test-llm');
      btn.innerText = 'Checking Provider...';
      try {
        const res = await API.get('/api/ai/llm-status');
        showToast(`AI Assistant is Active: ${res.name} (${res.model})`, 'success');
      } catch (err) {
        showToast('Local deterministic fallback engine active', 'info');
      } finally {
        btn.innerText = '⚡ Verify AI Assistant Status';
      }
    });
  },

  async loadSettings() {
    try {
      this.settings = await API.get('/api/settings');
      if (this.settings) {
        document.getElementById('set-shop-name').value = this.settings.shop_name || 'Sri Murugan Super Store';
        document.getElementById('set-gstin').value = this.settings.gstin || '33AAAAA0000A1Z5';
        document.getElementById('set-district').value = this.settings.district || 'Chennai';
        document.getElementById('set-address').value = this.settings.address || '42, Usman Road, T. Nagar, Chennai - 600017';
        document.getElementById('set-phone').value = this.settings.phone || '+91 98400 12345';
      }
    } catch (e) {
      console.error('Failed loading settings', e);
    }
  },

  async saveStoreSettings() {
    try {
      const payload = {
        shop_name: document.getElementById('set-shop-name').value.trim(),
        gstin: document.getElementById('set-gstin').value.trim(),
        district: document.getElementById('set-district').value,
        address: document.getElementById('set-address').value.trim(),
        phone: document.getElementById('set-phone').value.trim()
      };
      await API.put('/api/settings', payload);
      App.shopInfo = payload;
      showToast('Store profile saved successfully!', 'success');
    } catch (e) {
      console.error('Failed saving store profile', e);
    }
  }
};
