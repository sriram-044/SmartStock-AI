// ==============================================================================
// Inventory Management AI: API Client with Token Auth and Toast System
// ==============================================================================

const API = {
  baseUrl: '',

  getToken() {
    return localStorage.getItem('auth_token');
  },

  setToken(token) {
    if (token) localStorage.setItem('auth_token', token);
    else localStorage.removeItem('auth_token');
  },

  getUser() {
    const u = localStorage.getItem('auth_user');
    return u ? JSON.parse(u) : null;
  },

  setUser(user) {
    if (user) localStorage.setItem('auth_user', JSON.stringify(user));
    else localStorage.removeItem('auth_user');
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers
      });

      if (res.status === 401) {
        // Auto demo login if token expired or missing
        console.warn('Authentication needed. Logging in as default demo user...');
        await this.autoLoginDefault();
        // Retry once
        headers['Authorization'] = `Bearer ${this.getToken()}`;
        const retryRes = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
        if (!retryRes.ok) {
          const errData = await retryRes.json().catch(() => ({}));
          throw new Error(errData.detail || `Request failed with status ${retryRes.status}`);
        }
        return await retryRes.json();
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Request failed with status ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      showToast(err.message, 'error');
      throw err;
    }
  },

  get(endpoint, params = null) {
    let url = endpoint;
    if (params) {
      const q = new URLSearchParams();
      Object.keys(params).forEach(k => {
        if (params[k] !== null && params[k] !== undefined && params[k] !== '') {
          q.append(k, params[k]);
        }
      });
      const qs = q.toString();
      if (qs) url += `?${qs}`;
    }
    return this.request(url, { method: 'GET' });
  },

  post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  async autoLoginDefault() {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      if (res.ok) {
        const data = await res.json();
        this.setToken(data.access_token);
        this.setUser(data.user);
        return data.user;
      }
    } catch (e) {
      console.error('Auto-login failed', e);
    }
  }
};

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span style="flex:1;">${message}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
