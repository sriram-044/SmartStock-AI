// ==============================================================================
// Inventory Management AI: Localization & Indian Currency Formatter
// ==============================================================================

const I18N = {
  currentLang: localStorage.getItem('app_lang') || 'en',

  translations: {
    en: {
      app_title: "Inventory Management AI",
      app_subtitle: "An Agentic AI-Based Inventory Monitoring & Replenishment System",
      nav_dashboard: "Dashboard",
      nav_pos: "POS Billing",
      nav_products: "Products",
      nav_inventory: "Inventory Ledger",
      nav_recom: "AI Recommendations",
      nav_forecasting: "Demand Forecasting",
      nav_suppliers: "Suppliers",
      nav_expiry: "FEFO Expiry",
      nav_audits: "Stock Audits",
      nav_analytics: "Sales & Profit",
      nav_reports: "Reports",
      
      kpi_total_products: "Total Products",
      kpi_inventory_qty: "Total Units in Stock",
      kpi_inventory_val: "Inventory Valuation",
      kpi_today_sales: "Today's Sales",
      kpi_today_profit: "Today's Gross Profit",
      kpi_critical_stock: "Critical Stockouts",
      kpi_low_stock: "Reorder Soon",
      kpi_pending_recom: "Pending AI Actions",
      
      btn_approve: "Approve Order",
      btn_reject: "Reject",
      btn_modify: "Modify Qty",
      btn_explain: "View Reasoning",
      btn_scan_ai: "Run Agent Scan",
      btn_checkout: "Complete Checkout",
      btn_clear_cart: "Clear Cart",
      
      status_critical: "Critical Risk",
      status_reorder_now: "Reorder Now",
      status_reorder_soon: "Reorder Soon",
      status_safe: "Safe Stock",
      status_overstock: "Overstock",
      status_dead_stock: "Dead Stock"
    },
    ta: {
      app_title: "இன்வெண்டரி மேனேஜ்மென்ட் AI",
      app_subtitle: "செயற்கை நுண்ணறிவு அடிப்படையிலான இருப்பு கண்காணிப்பு மற்றும் மறுஆர்டர் முறைமை",
      nav_dashboard: "முதன்மை பலகை",
      nav_pos: "பில்லிங் விற்பனை (POS)",
      nav_products: "பொருட்கள் பட்டியல்",
      nav_inventory: "இருப்பு பதிவேடு",
      nav_recom: "AI பரிந்துரைகள்",
      nav_forecasting: "தேவை கணிப்பு",
      nav_suppliers: "விநியோகஸ்தர்கள்",
      nav_expiry: "காலாவதி கண்காணிப்பு",
      nav_audits: "நேரடி இருப்பு தணிக்கை",
      nav_analytics: "விற்பனை & லாபம்",
      nav_reports: "அறிக்கைகள்",
      
      kpi_total_products: "மொத்த பொருட்கள்",
      kpi_inventory_qty: "கையிருப்பு அலகுகள்",
      kpi_inventory_val: "மொத்த இருப்பு மதிப்பு",
      kpi_today_sales: "இன்றைய விற்பனை",
      kpi_today_profit: "இன்றைய லாபம்",
      kpi_critical_stock: "அபாயகரமான இருப்பு",
      kpi_low_stock: "மறுஆர்டர் தேவை",
      kpi_pending_recom: "நிலுவையிலுள்ள பரிந்துரைகள்",
      
      btn_approve: "ஆர்டரை அங்கீகரி",
      btn_reject: "நிராகரி",
      btn_modify: "அளவை மாற்று",
      btn_explain: "காரணம் காண்க",
      btn_scan_ai: "AI ஆய்வு செய்க",
      btn_checkout: "பில் போடுக",
      btn_clear_cart: "கார்ட்டை காலியாக்கு",
      
      status_critical: "மிகக் குறைவான இருப்பு",
      status_reorder_now: "உடனடி மறுஆர்டர்",
      status_reorder_soon: "மறுஆர்டர் தேவை",
      status_safe: "பாதுகாப்பான இருப்பு",
      status_overstock: "அதிக இருப்பு",
      status_dead_stock: "முடங்கிய இருப்பு"
    }
  },

  t(key) {
    const dict = this.translations[this.currentLang] || this.translations.en;
    return dict[key] || this.translations.en[key] || key;
  },

  setLang(lang) {
    this.currentLang = lang;
    localStorage.setItem('app_lang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (key) el.innerText = this.t(key);
    });
    // Trigger custom event
    window.dispatchEvent(new CustomEvent('lang-changed', { detail: { lang } }));
  }
};

/**
 * Formats numbers in Indian Rupee format (₹, Lakhs, Crores)
 * e.g., 125000 -> ₹1,25,000.00
 * e.g., 12500000 (compact) -> ₹1.25 Cr
 */
function formatINR(val, compact = false) {
  if (val === null || val === undefined || isNaN(val)) return '₹0.00';
  const num = Number(val);
  
  if (compact) {
    if (Math.abs(num) >= 10000000) {
      return '₹' + (num / 10000000).toFixed(2) + ' Cr';
    }
    if (Math.abs(num) >= 100000) {
      return '₹' + (num / 100000).toFixed(2) + ' Lakh';
    }
  }

  // Exact Indian grouping algorithm
  const parts = num.toFixed(2).split('.');
  let integerPart = parts[0];
  const decimalPart = parts[1];
  const isNegative = integerPart.startsWith('-');
  if (isNegative) integerPart = integerPart.substring(1);

  let lastThree = integerPart.substring(integerPart.length - 3);
  let otherNumbers = integerPart.substring(0, integerPart.length - 3);
  if (otherNumbers !== '') {
    lastThree = ',' + lastThree;
  }
  const formattedInteger = otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + lastThree;

  return (isNegative ? '-₹' : '₹') + formattedInteger + '.' + decimalPart;
}
