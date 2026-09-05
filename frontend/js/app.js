// ==============================================================================
// Inventory Management AI: Master Application Orchestrator & Router
// ==============================================================================

const App = {
  currentView: 'dashboard',
  currentUser: null,
  shopInfo: null,

  async init() {
    console.log('[App] Initializing Inventory Management AI...');

    // Auto-login default demo user if needed
    this.currentUser = API.getUser();
    if (!this.currentUser) {
      this.currentUser = await API.autoLoginDefault();
    }
    this.updateUserUI();

    // Load shop profile
    try {
      this.shopInfo = await API.get('/api/settings');
    } catch (e) {
      console.warn('Could not fetch settings', e);
    }

    // Initialize Language
    const currentLang = localStorage.getItem('app_lang') || 'en';
    I18N.setLang(currentLang);
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
      langSelect.value = currentLang;
      langSelect.addEventListener('change', (e) => {
        I18N.setLang(e.target.value);
        this.renderCurrentView();
      });
    }

    // Initialize Regional District selector
    const distSelect = document.getElementById('district-select');
    if (distSelect && this.shopInfo) {
      distSelect.value = this.shopInfo.district || 'Chennai';
      distSelect.addEventListener('change', async (e) => {
        const newDist = e.target.value;
        try {
          await API.put('/api/settings', {
            ...this.shopInfo,
            district: newDist
          });
          showToast(`Store location set to ${newDist}, Tamil Nadu`, 'info');
        } catch (err) {}
      });
    }

    // Role switcher simulation in topbar/profile
    const roleSelect = document.getElementById('role-switcher');
    if (roleSelect && this.currentUser) {
      roleSelect.value = this.currentUser.role;
      roleSelect.addEventListener('change', async (e) => {
        const role = e.target.value;
        // Switch user credentials
        const creds = {
          admin: { username: 'admin', password: 'admin123' },
          manager: { username: 'manager', password: 'manager123' },
          cashier: { username: 'cashier', password: 'cashier123' }
        }[role];
        if (creds) {
          try {
            const res = await fetch('/api/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(creds)
            });
            const data = await res.json();
            API.setToken(data.access_token);
            API.setUser(data.user);
            App.currentUser = data.user;
            App.updateUserUI();
            showToast(`Switched active role to: ${data.user.full_name} (${role.toUpperCase()})`, 'info');
          } catch (err) {}
        }
      });
    }

    // Initialize AI Chat Drawer
    AIChatDrawer.init();

    // Setup Hash Routing
    window.addEventListener('hashchange', () => this.handleRouting());
    this.handleRouting();

    // Setup Navigation Item Click Listeners
    document.querySelectorAll('.nav-item').forEach(el => {
      el.addEventListener('click', () => {
        const view = el.getAttribute('data-view');
        if (view) this.navigate(view);
      });
    });
  },

  updateUserUI() {
    if (!this.currentUser) return;
    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-role-tag');
    const avatarEl = document.getElementById('user-avatar');

    if (nameEl) nameEl.innerText = this.currentUser.full_name;
    if (roleEl) roleEl.innerText = this.currentUser.role.toUpperCase();
    if (avatarEl) avatarEl.innerText = this.currentUser.full_name.charAt(0);
  },

  handleRouting() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    this.navigate(hash, false);
  },

  navigate(viewName, updateHash = true) {
    this.currentView = viewName;
    if (updateHash) {
      window.location.hash = viewName;
    }

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(el => {
      if (el.getAttribute('data-view') === viewName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Update page title
    const titles = {
      dashboard: 'Dashboard',
      pos: 'POS Billing Terminal',
      products: 'Product Management',
      inventory: 'Inventory Ledger',
      'ai-recom': 'AI Recommendations',
      forecasting: 'Demand Forecasting',
      suppliers: 'Supplier Intelligence',
      expiry: 'FEFO Expiry',
      audits: 'Stock Audits',
      analytics: 'Sales Analytics',
      reports: 'Business Reports'
    };
    const titleEl = document.getElementById('page-current-title');
    if (titleEl) {
      titleEl.innerText = titles[viewName] || 'Inventory AI';
    }

    this.renderCurrentView();
  },

  async renderCurrentView() {
    const container = document.getElementById('main-content-container');
    if (!container) return;

    window.scrollTo({ top: 0, behavior: 'smooth' });

    switch (this.currentView) {
      case 'dashboard':
        await DashboardView.render(container);
        break;
      case 'pos':
        await POSView.render(container);
        break;
      case 'products':
        await ProductsView.render(container);
        break;
      case 'inventory':
        await InventoryView.render(container);
        break;
      case 'ai-recom':
        await AIRecomView.render(container);
        break;
      case 'forecasting':
        await ForecastingView.render(container);
        break;
      case 'suppliers':
        await SuppliersView.render(container);
        break;
      case 'expiry':
        await ExpiryView.render(container);
        break;
      case 'audits':
        await AuditsView.render(container);
        break;
      case 'analytics':
        await AnalyticsView.render(container);
        break;
      case 'reports':
        await ReportsView.render(container);
        break;
      default:
        await DashboardView.render(container);
    }
  },

  openModal() {
    const modal = document.getElementById('app-modal');
    if (modal) modal.classList.add('active');
  },

  closeModal() {
    const modal = document.getElementById('app-modal');
    if (modal) modal.classList.remove('active');
  },

  async approveRecommendation(recomId) {
    await AIRecomView.approve(recomId);
    if (this.currentView === 'dashboard') {
      await DashboardView.loadData();
    }
  }
};

// Auto-boot on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
