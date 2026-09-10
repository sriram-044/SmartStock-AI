// ==============================================================================
// Inventory Management AI: Visual Assets & SVG Product Illustrations
// Authentic illustrations for Indian retail grocery SKUs & categories
// ==============================================================================

const Assets = {
  // Returns an SVG string for a given product or category
  getProductImage(productName = '', categoryName = '') {
    const name = (productName || '').toLowerCase();
    const cat = (categoryName || '').toLowerCase();

    // 1. Rice & Grains
    if (name.includes('rice') || name.includes('arisi') || name.includes('ponni') || name.includes('basmati') || name.includes('sona')) {
      return this.svgRiceBag(name.includes('ponni') ? 'Ponni Rice' : 'Rice');
    }
    // 2. Salt
    if (name.includes('salt') || name.includes('uppu') || name.includes('tata')) {
      return this.svgSaltPack();
    }
    // 3. Cooking Oil & Ghee
    if (name.includes('oil') || name.includes('ennai') || name.includes('gold winner') || name.includes('sunflower') || name.includes('gingelly') || name.includes('ghee')) {
      return this.svgOilBottle();
    }
    // 4. Detergent & Cleaning
    if (name.includes('surf') || name.includes('detergent') || name.includes('washing') || name.includes('powder') || name.includes('ariel') || name.includes('rin')) {
      return this.svgDetergentPack();
    }
    // 5. Atta, Maida, Flours
    if (name.includes('atta') || name.includes('flour') || name.includes('aashirvaad') || name.includes('maida') || name.includes('rava')) {
      return this.svgAttaBag();
    }
    // 6. Dals & Pulses
    if (name.includes('dal') || name.includes('paruppu') || name.includes('toor') || name.includes('urad') || name.includes('moong') || name.includes('chana')) {
      return this.svgDalPack();
    }
    // 7. Spices & Masalas
    if (name.includes('masala') || name.includes('chilli') || name.includes('turmeric') || name.includes('sambar') || name.includes('coriander') || name.includes('pepper') || name.includes('sakthi') || name.includes('aachi')) {
      return this.svgSpicePack();
    }
    // 8. Soap, Shampoo & Personal Care
    if (name.includes('soap') || name.includes('shampoo') || name.includes('clinic') || name.includes('hamam') || name.includes('lux') || name.includes('santoor') || name.includes('dettol') || name.includes('paste')) {
      return this.svgSoapBottle();
    }
    // 9. Biscuits, Snacks & Beverages
    if (name.includes('biscuit') || name.includes('tea') || name.includes('coffee') || name.includes('maggi') || name.includes('noodles') || name.includes('3 roses') || name.includes('bru') || name.includes('parle')) {
      return this.svgSnackPack();
    }
    // 10. Dairy
    if (name.includes('milk') || name.includes('curd') || name.includes('butter') || name.includes('paneer') || name.includes('aavin') || name.includes('amul')) {
      return this.svgDairyPack();
    }

    // Default based on category
    if (cat.includes('grain') || cat.includes('staple')) return this.svgRiceBag('Staple');
    if (cat.includes('oil')) return this.svgOilBottle();
    if (cat.includes('clean') || cat.includes('household')) return this.svgDetergentPack();
    if (cat.includes('snack') || cat.includes('beverage')) return this.svgSnackPack();
    if (cat.includes('personal') || cat.includes('care')) return this.svgSoapBottle();

    return this.svgGeneralGrocery();
  },

  svgRiceBag(label = 'Rice') {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <defs>
        <linearGradient id="riceGrad" x1="20" y1="20" x2="100" y2="110" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FDE68A"/>
          <stop offset="1" stop-color="#D97706"/>
        </linearGradient>
        <linearGradient id="riceCloth" x1="30" y1="35" x2="90" y2="105" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FEF3C7"/>
          <stop offset="1" stop-color="#FBBF24"/>
        </linearGradient>
      </defs>
      <rect x="25" y="32" width="70" height="74" rx="14" fill="url(#riceCloth)" stroke="#D97706" stroke-width="2.5"/>
      <path d="M30 32 C30 20, 90 20, 90 32 Z" fill="#F59E0B" stroke="#B45309" stroke-width="2"/>
      <path d="M42 22 L78 22" stroke="#B45309" stroke-width="3" stroke-linecap="round"/>
      <rect x="35" y="48" width="50" height="36" rx="6" fill="#FFFFFF" opacity="0.92"/>
      <circle cx="60" cy="60" r="10" fill="#EF4444" opacity="0.15"/>
      <path d="M56 56 Q60 52 64 56 Q68 60 64 64 Q60 68 56 64 Z" fill="#EF4444"/>
      <text x="60" y="78" font-family="Inter, sans-serif" font-size="8.5" font-weight="bold" fill="#1F2937" text-anchor="middle">${label}</text>
      <path d="M35 96 Q60 102 85 96" stroke="#D97706" stroke-width="2" stroke-linecap="round"/>
    </svg>`;
  },

  svgSaltPack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <defs>
        <linearGradient id="saltGrad" x1="25" y1="20" x2="95" y2="110" gradientUnits="userSpaceOnUse">
          <stop stop-color="#EA580C"/>
          <stop offset="0.6" stop-color="#F97316"/>
          <stop offset="1" stop-color="#C2410C"/>
        </linearGradient>
      </defs>
      <rect x="28" y="24" width="64" height="82" rx="10" fill="url(#saltGrad)" stroke="#9A3412" stroke-width="2"/>
      <rect x="34" y="38" width="52" height="42" rx="6" fill="#FFFFFF"/>
      <path d="M42 54 Q60 46 78 54 Q60 62 42 54 Z" fill="#EA580C"/>
      <text x="60" y="57" font-family="Outfit, sans-serif" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">TATA</text>
      <text x="60" y="72" font-family="Inter, sans-serif" font-size="8" font-weight="bold" fill="#EA580C" text-anchor="middle">SALT</text>
      <circle cx="60" cy="94" r="5" fill="#FED7AA"/>
      <path d="M36 28 L84 28" stroke="#FFFFFF" stroke-width="2" stroke-dasharray="3 3"/>
    </svg>`;
  },

  svgOilBottle() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <defs>
        <linearGradient id="oilGrad" x1="35" y1="35" x2="85" y2="110" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FBBF24"/>
          <stop offset="0.5" stop-color="#F59E0B"/>
          <stop offset="1" stop-color="#D97706"/>
        </linearGradient>
      </defs>
      <rect x="52" y="16" width="16" height="12" rx="3" fill="#EF4444"/>
      <path d="M50 28 L70 28 L78 44 L78 102 C78 106 74 110 70 110 L50 110 C46 110 42 106 42 102 L42 44 Z" fill="url(#oilGrad)" stroke="#B45309" stroke-width="2"/>
      <rect x="46" y="54" width="28" height="34" rx="4" fill="#FFFFFF" opacity="0.95"/>
      <circle cx="60" cy="68" r="8" fill="#F59E0B" opacity="0.2"/>
      <circle cx="60" cy="68" r="4" fill="#EF4444"/>
      <text x="60" y="83" font-family="Inter, sans-serif" font-size="6.5" font-weight="bold" fill="#1F2937" text-anchor="middle">OIL 1L</text>
      <path d="M46 96 Q60 99 74 96" stroke="#B45309" stroke-width="1.5"/>
    </svg>`;
  },

  svgDetergentPack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <defs>
        <linearGradient id="detGrad" x1="20" y1="20" x2="100" y2="110" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563EB"/>
          <stop offset="0.5" stop-color="#1D4ED8"/>
          <stop offset="1" stop-color="#1E40AF"/>
        </linearGradient>
      </defs>
      <rect x="26" y="24" width="68" height="82" rx="12" fill="url(#detGrad)" stroke="#1E3A8A" stroke-width="2.5"/>
      <path d="M26 40 Q60 55 94 35 L94 24 L26 24 Z" fill="#3B82F6" opacity="0.6"/>
      <rect x="34" y="44" width="52" height="38" rx="6" fill="#FFFFFF"/>
      <path d="M42 56 L50 50 L60 62 L70 48 L78 58" stroke="#EF4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="60" y="76" font-family="Outfit, sans-serif" font-size="8.5" font-weight="900" fill="#2563EB" text-anchor="middle">SURF EXCEL</text>
      <circle cx="82" cy="94" r="6" fill="#22C55E"/>
      <path d="M79 94 L81 96 L85 92" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
    </svg>`;
  },

  svgAttaBag() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <defs>
        <linearGradient id="attaGrad" x1="30" y1="25" x2="90" y2="105" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FCD34D"/>
          <stop offset="1" stop-color="#F59E0B"/>
        </linearGradient>
      </defs>
      <rect x="28" y="28" width="64" height="78" rx="10" fill="url(#attaGrad)" stroke="#B45309" stroke-width="2"/>
      <path d="M28 28 C28 18, 92 18, 92 28 Z" fill="#D97706"/>
      <rect x="36" y="42" width="48" height="40" rx="5" fill="#FFFFFF"/>
      <circle cx="60" cy="58" r="10" fill="#DC2626"/>
      <text x="60" y="61" font-family="Outfit, sans-serif" font-size="7" font-weight="bold" fill="#FFFFFF" text-anchor="middle">100%</text>
      <text x="60" y="76" font-family="Inter, sans-serif" font-size="7.5" font-weight="bold" fill="#B45309" text-anchor="middle">ATTA</text>
    </svg>`;
  },

  svgDalPack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <rect x="28" y="26" width="64" height="80" rx="10" fill="#FEF08A" stroke="#CA8A04" stroke-width="2.5"/>
      <rect x="36" y="38" width="48" height="42" rx="6" fill="#FFFFFF"/>
      <circle cx="50" cy="54" r="5" fill="#EAB308"/>
      <circle cx="62" cy="52" r="6" fill="#F59E0B"/>
      <circle cx="70" cy="58" r="4.5" fill="#D97706"/>
      <text x="60" y="74" font-family="Inter, sans-serif" font-size="8" font-weight="bold" fill="#854D0E" text-anchor="middle">TOOR DAL</text>
    </svg>`;
  },

  svgSpicePack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <rect x="28" y="25" width="64" height="80" rx="8" fill="#DC2626" stroke="#991B1B" stroke-width="2"/>
      <rect x="36" y="38" width="48" height="40" rx="4" fill="#FEF2F2"/>
      <path d="M52 50 Q60 42 68 50 Q60 62 52 50 Z" fill="#DC2626"/>
      <text x="60" y="72" font-family="Outfit, sans-serif" font-size="7.5" font-weight="bold" fill="#991B1B" text-anchor="middle">MASALA</text>
    </svg>`;
  },

  svgSoapBottle() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <rect x="52" y="18" width="16" height="10" rx="3" fill="#6C63FF"/>
      <path d="M48 28 L72 28 L80 46 L80 98 C80 104 74 108 68 108 L52 108 C46 108 40 104 40 98 L40 46 Z" fill="#8B5CF6" stroke="#6D28D9" stroke-width="2"/>
      <rect x="46" y="52" width="28" height="34" rx="4" fill="#FFFFFF"/>
      <circle cx="60" cy="66" r="6" fill="#C4B5FD"/>
      <text x="60" y="80" font-family="Inter, sans-serif" font-size="6" font-weight="bold" fill="#6D28D9" text-anchor="middle">CARE</text>
    </svg>`;
  },

  svgSnackPack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <rect x="25" y="30" width="70" height="70" rx="10" fill="#F97316" stroke="#C2410C" stroke-width="2"/>
      <rect x="34" y="42" width="52" height="36" rx="4" fill="#FEF3C7"/>
      <circle cx="50" cy="56" r="6" fill="#F59E0B"/>
      <circle cx="68" cy="56" r="6" fill="#F59E0B"/>
      <text x="60" y="73" font-family="Outfit, sans-serif" font-size="7.5" font-weight="bold" fill="#C2410C" text-anchor="middle">SNACKS</text>
    </svg>`;
  },

  svgDairyPack() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <path d="M40 38 L60 20 L80 38 L80 104 C80 108 76 110 72 110 L48 110 C44 110 40 108 40 104 Z" fill="#38BDF8" stroke="#0284C7" stroke-width="2"/>
      <rect x="46" y="52" width="28" height="34" rx="4" fill="#FFFFFF"/>
      <text x="60" y="72" font-family="Outfit, sans-serif" font-size="8" font-weight="bold" fill="#0284C7" text-anchor="middle">MILK</text>
    </svg>`;
  },

  svgGeneralGrocery() {
    return `<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" class="prod-svg-asset">
      <rect x="28" y="28" width="64" height="76" rx="10" fill="#E2E8F0" stroke="#94A3B8" stroke-width="2"/>
      <rect x="36" y="40" width="48" height="40" rx="6" fill="#FFFFFF"/>
      <circle cx="60" cy="56" r="8" fill="#CBD5E1"/>
      <text x="60" y="74" font-family="Inter, sans-serif" font-size="7.5" font-weight="bold" fill="#475569" text-anchor="middle">ITEM</text>
    </svg>`;
  }
};
