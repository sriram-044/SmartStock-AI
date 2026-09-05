# Inventory Management AI

> **Subtitle**: An Agentic AI-Based Intelligent Inventory Monitoring, Demand Forecasting and Replenishment System  
> **Target Region**: India (Specialized for Tamil Nadu & South Indian Retail Business Practices)  
> **Currency**: Indian Rupee (₹ / INR)

---

## 🌟 Overview

**Inventory Management AI** is a complete, production-quality, intelligent retail inventory decision-support platform designed specifically for small, medium, and supermarket retail shops in India, with specialized adaptation for Tamil Nadu and South Indian business practices.

Unlike conventional CRUD inventory applications that act as static record ledgers, this platform integrates an **autonomous Agentic AI decision engine** that continuously monitors sales velocity, evaluates stockout risks against supplier delivery turnaround, forecasts forward demand using comparative Machine Learning models, and generates transparent replenishment orders with human-in-the-loop approval.

---

## ✨ Key Capabilities

1. **Autonomous Agentic AI Decision Loop**:
   - **Observe**: Monitors real-time stock levels, daily sales velocity, supplier lead times, batch expiry dates, and physical audit variances.
   - **Analyze**: Computes Average Daily Sales (ADS), demand volatility ($\sigma_D$), and Days of Inventory Remaining ($DIR$).
   - **Forecast**: Projects future demand across 1-day, 7-day, and 30-day horizons.
   - **Identify Risk**: Classifies inventory into **CRITICAL**, **REORDER NOW**, **REORDER SOON**, **SAFE**, **OVERSTOCK**, or **DEAD STOCK**.
   - **Reason**: Multi-criteria supplier ranking (balances lead-time urgency during critical shortages vs. wholesale price discounts during routine replenishments).
   - **Decide & Recommend**: Generates transparent replenishment cards showing the exact mathematical breakdown.
   - **Human-In-The-Loop**: Shopkeeper can approve, modify order quantity, or reject with override reason.
   - **Outcome Feedback**: Tracks post-decision sales and continuously refines model accuracy.

2. **Machine Learning Demand Forecasting**:
   - Comparative evaluation of three algorithms:
     1. **Weighted Moving Average Baseline** (7-day and 14-day rolling window)
     2. **Multi-variable Linear Regression** (trend, day-of-week, weekend effects, festival flags)
     3. **Random Forest Regressor** (lagged demand $t-1, t-7, t-14$, rolling mean & volatility, calendar spikes)
   - Dynamic model selector: automatically chooses the best performing algorithm per product based on validation MAE / RMSE.

3. **Transparent Reorder & Statistical Safety Stock**:
   - No opaque black boxes. Every recommendation exposes the exact mathematical calculation in the UI:
     $$\text{Safety Stock} = Z \times \sigma_D \times \sqrt{L}$$
     $$\text{Lead-Time Demand (LTD)} = \text{ADS} \times L$$
     $$\text{Target Stock} = \text{LTD} + \text{Safety Stock}$$
     $$\text{Recommended Order} = \max(\text{Target Stock} - \text{Current Stock}, \text{MOQ})$$

4. **India & Tamil Nadu Regional Localization**:
   - All financial metrics formatted in **Indian Rupees (₹)** with Lakhs and Crores (`₹1,25,000.00`).
   - Configurable Indian GST rates (0%, 5%, 12%, 18%, 28%) with automatic **CGST & SGST** tax invoice split.
   - Regional location selector covering all **38 Tamil Nadu districts** (Chennai, Coimbatore, Madurai, Salem, Tiruchirappalli, Erode, Tiruppur, Tirunelveli, Vellore, Thanjavur, Hosur/Krishnagiri, etc.).
   - Bilingual support: Primary English UI with **Tamil names** for products, categories, alerts, and AI reasoning summaries.

5. **Integrated Retail POS Billing Terminal**:
   - Fast barcode scanner support and real-time inventory safeguard (prevents selling more than physical shelf stock).
   - Instant cart preview with GST breakdown, item discounts, and multiple payment methods: **Cash, UPI (GPay/PhonePe QR code simulator), Debit Card, Credit Card, Khata/Credit**.
   - Printable thermal invoice receipt in standard Indian retail format.

6. **FEFO Expiry & Markdown Management**:
   - First-Expired, First-Out (FEFO) batch tracking with days-to-expiry countdown.
   - Projects unsold inventory at expiry date based on sales velocity and suggests clearance markdown discounts.

7. **Physical Stock Audits & Discrepancy Diagnostics**:
   - Compares physical count vs. system recorded stock.
   - AI diagnostics identify likely causes (transit damage, cashier scan error, supplier box miscount) with neutral, professional wording.
   - One-click atomic reconciliation in the ledger.

8. **Natural Language AI Assistant**:
   - Slide-over assistant drawer answering real-world retail questions using live database tools:
     - *"Which products need immediate restocking?"*
     - *"Why is shampoo marked as critical?"*
     - *"Which products are not selling?"*
     - *"Which supplier is best for rice?"*
     - *"How much inventory value is currently blocked in dead stock?"*

---

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | SQLite3 (WAL Mode, Relational Foreign Keys, Atomic Transactions) |
| **Machine Learning** | scikit-learn, NumPy, Pandas, SciPy |
| **Frontend** | HTML5, Vanilla CSS (Custom Design System, Glassmorphism, Responsive Grid), Vanilla JavaScript (Modular Single Page Application) |
| **Visualization** | Custom Canvas/SVG Charting Engine (Line/Area Trends, Donut Charts, Forecast Curves) |
| **Authentication** | PBKDF2 Password Hashing with Salt, Signed JWT Tokens, Role-Based Access Control (Admin, Manager, Cashier) |

---

## 🚀 Quickstart & Installation

### 1. Clone & Setup Environment
```bash
# Verify Python version (Python 3.10+ recommended)
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database & Seed Demo Data
The database is automatically initialized and seeded on first run with 55+ Indian retail products across 7 categories, 10 Tamil Nadu wholesale suppliers, and 180 days of historical sales. To re-seed manually:
```bash
python -m data.seed_data
```

### 3. (Optional) Configure Free LLM Copilot (Gemini / Groq / Ollama)
SmartStock-AI works **100% locally out-of-the-box** with zero configuration required.
If you want to enable free cloud LLM conversational capabilities with native Agent Tool Calling:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your free API key in `.env`:
   - **Google Gemini (Recommended & 100% Free)**: Get key from [Google AI Studio](https://aistudio.google.com/) and set `GEMINI_API_KEY=AIzaSy...`
   - **Groq Cloud (Ultra-Fast & 100% Free)**: Get key from [Groq Console](https://console.groq.com/) and set `GROQ_API_KEY=gsk_...`
   - **Ollama (100% Free Offline Local)**: Install [Ollama](https://ollama.com/) and run `ollama run llama3.2`

### 4. Run Application Server
```bash
python run_server.py
```
Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## 👥 Demo User Accounts

| Role | Username | Password | Permissions |
|---|---|---|---|
| **Admin (Owner)** | `admin` | `admin123` | Full access: users, products, suppliers, rules, approvals, reports, AI settings |
| **Store Manager** | `manager` | `manager123` | Inventory ledger, approvals, suppliers, stock audits, reports |
| **Cashier** | `cashier` | `cashier123` | POS billing terminal, sales lookup, customer returns |

---

## 🧪 Automated Testing

Execute the comprehensive automated test suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Test coverage includes:
- `tests/test_inventory_ledger.py`: Verifies atomic transactions and negative stock protection.
- `tests/test_pos_billing.py`: Verifies cart calculation, GST split, and customer returns.
- `tests/test_forecasting_models.py`: Verifies Moving Average, Linear Regression, and Random Forest accuracy.
- `tests/test_reorder_and_suppliers.py`: Verifies statistical safety stock, dead stock, and FEFO expiry.
- `tests/test_agent_and_ai.py`: Verifies Observe-Analyze-Decide cycle, approval gateway, and natural language assistant.
- `tests/test_auth_and_roles.py`: Verifies password hashing, token validation, and RBAC permissions.

---

## 📄 License & Academic Attribution
Developed as an advanced IoC / Capstone Project demonstrating Agentic AI in retail supply chain systems.
