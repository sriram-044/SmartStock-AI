// ==============================================================================
// Inventory Management AI: Master Application Orchestrator & Router
// Designed for Tamil Nadu Retail AI Operations
// ==============================================================================

const App = {
  currentView: 'dashboard',
  currentUser: null,
  shopInfo: null,

  async init() {
    console.log('[App] Initializing Inventory Management AI (Modern Light SaaS)...');

    // Auto-login default demo user (Cashier or Admin)
    this.currentUser = API.getUser();
    if (!this.currentUser) {
      this.currentUser = await API.autoLoginDefault();
    }
    this.updateUserUI();

    // Load shop profile
    try {
      this.shopInfo = await API.get('/api/settings');
      this.updateShopUI();
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
          this.shopInfo.district = newDist;
          this.updateShopUI();
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
            showToast(`Switched active user to: ${data.user.full_name} (${role.toUpperCase()})`, 'info');
            App.renderCurrentView();
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

    // Keyboard Hotkeys for Fast Retail Operations
    window.addEventListener('keydown', (e) => {
      if (e.key === 'F2') {
        e.preventDefault();
        this.navigate('pos');
      } else if (e.key === 'F1') {
        e.preventDefault();
        this.navigate('dashboard');
      } else if (e.key === 'F3') {
        e.preventDefault();
        this.navigate('ai-recom');
      } else if (e.key === 'Escape') {
        this.closeModal();
        AIChatDrawer.closeDrawer();
      }
    });
  },

  updateShopUI() {
    if (!this.shopInfo) return;
    const shopName = this.shopInfo.shop_name || 'Sri Murugan Super Store';
    const district = this.shopInfo.district || 'Chennai';

    const sidebarName = document.getElementById('sidebar-shop-name');
    if (sidebarName) sidebarName.innerText = shopName;

    const sidebarLoc = document.getElementById('sidebar-shop-loc');
    if (sidebarLoc) {
      sidebarLoc.innerHTML = `<span>${district}, Tamil Nadu</span> &bull; <span style="color: #10B981; font-weight: bold;">● Online</span>`;
    }

    const subtitleEl = document.getElementById('page-current-subtitle');
    if (subtitleEl) {
      subtitleEl.innerText = `${shopName} — ${district}, Tamil Nadu`;
    }
  },

  updateUserUI() {
    if (!this.currentUser) return;
    const fullName = this.currentUser.full_name || 'Sriram';
    const role = (this.currentUser.role || 'manager').toUpperCase();
    const initial = fullName.charAt(0);

    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-role-tag');
    const avatarEl = document.getElementById('user-avatar');
    const topAvatar = document.getElementById('topbar-avatar');
    const topName = document.getElementById('topbar-username');

    if (nameEl) nameEl.innerText = fullName;
    if (roleEl) roleEl.innerText = role;
    if (avatarEl) avatarEl.innerText = initial;
    if (topAvatar) topAvatar.innerText = initial;
    if (topName) topName.innerText = fullName;
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
      'agent-workspace': 'Agentic AI Workspace & Command Center',
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
      reports: 'Business Reports',
      settings: 'Store & AI Settings'
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
      case 'agent-workspace':
        await AgentWorkspaceView.render(container);
        break;
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
      case 'settings':
        await SettingsView.render(container);
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
