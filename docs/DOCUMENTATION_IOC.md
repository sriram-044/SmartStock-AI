# ACADEMIC PROJECT REPORT
## INVENTORY MANAGEMENT AI
### An Agentic AI-Based Intelligent Inventory Monitoring, Demand Forecasting and Replenishment System
**Domain**: Agentic Artificial Intelligence & Retail Supply Chain Optimization  
**Target Market**: Indian Retail Sector (Special Focus: Tamil Nadu & South India)

---

## 1. ABSTRACT

Retail inventory management in small and medium-sized Indian enterprises (SMEs) has historically relied on manual physical verification, static reorder thresholds, or fragmented ledger books. These methods fail to cope with seasonal demand volatility (such as Pongal, Deepavali, and wedding seasons), supplier delivery delays, perishable goods expiration, and dead stock capital lock-in.

This project introduces **Inventory Management AI**, a comprehensive, production-quality, agentic decision-support platform designed to bridge the gap between traditional retail operations and autonomous machine intelligence. The system employs an **autonomous Agentic AI decision engine** operating on an Observe-Analyze-Forecast-Reason-Decide feedback loop. By integrating statistical safety-stock modeling, multi-model Machine Learning demand forecasting (comparing Weighted Moving Average, Linear Regression, and Random Forest regressors), multi-attribute supplier scoring, First-Expired-First-Out (FEFO) shelf-life optimization, and physical audit discrepancy diagnostics, the platform transforms inventory management from passive record-keeping into proactive replenishment optimization. All monetary metrics adhere strictly to the Indian numbering system and Rupee currency (₹ / INR), with configurable GST tax slabs (CGST/SGST splits) and bilingual English-Tamil support.

---

## 2. INTRODUCTION

The Indian retail sector is one of the most vibrant and fast-paced industries in the world, contributing over 10% to the country's GDP. In South India, and particularly Tamil Nadu, neighborhood provision stores (*Maligai Saman Kadai*), supermarkets, FMCG outlets, and specialty retailers handle high transaction volumes across thousands of distinct Stock Keeping Units (SKUs), ranging from daily staples (rice, pulses, edible oils) to personal care, packaged foods, and household cleaners.

Despite the digital revolution driven by UPI and GST compliance, inventory replenishment in Indian retail remains largely intuitive and unscientific. Shopkeepers frequently encounter two diametrically opposed failure modes:
1. **Stockouts**: Running out of critical fast-moving staples during peak hours or festival surges, directly losing customer goodwill and revenue.
2. **Overstock and Dead Stock**: Tying up scarce working capital in slow-moving items that occupy premium shelf space or expire before sale.

**Inventory Management AI** addresses these challenges by embedding an intelligent, explainable agent directly into the daily retail operational workflow.

---

## 3. PROBLEM STATEMENT

Conventional retail Point of Sale (POS) and inventory management systems suffer from several critical shortcomings:
1. **Lack of Predictive Foresight**: Existing software records what *has* been sold, but cannot reliably project what *will* be sold tomorrow, next week, or next month.
2. **Fixed Reorder Level Inflexibility**: Setting a static minimum threshold (e.g., "reorder when stock falls below 20") ignores supplier lead time variations, seasonal festival spikes, and sales velocity shifts.
3. **Opaque and Black-Box Systems**: Shopkeepers reject automated systems that issue arbitrary commands ("Order 50 units") without showing the underlying mathematical reasoning.
4. **Disconnection from Local Practices**: Western ERPs use USD currency, non-GST tax models, lack Indian numbering (Lakhs/Crores), and provide no support for regional languages or festival cycles (Pongal, Deepavali, Aadi Perukku).
5. **Absence of Autonomous Reasoning**: Typical software requires human managers to manually sift through hundreds of rows to identify expiring batches, dead stock, and supplier discrepancies.

---

## 4. PROJECT OBJECTIVES

The primary objective of this project is to develop and deploy an **Agentic AI Decision-Support Platform** tailored for Indian retail:
- **Intelligent Stock Monitoring**: Maintain an immutable, atomic inventory transaction ledger tracking Opening balances, Purchases (+), Returns (+), Sales (-), Damaged (-), Expired (-), and Audit Adjustments (±).
- **Explainable ML Demand Forecasting**: Train and compare multiple ML models (Moving Average, Linear Regression, Random Forest Regressor) and dynamically select the optimal model per SKU.
- **Stockout & Lead-Time Prediction**: Calculate Days of Inventory Remaining ($DIR = \frac{\text{Current Stock}}{\text{Average Daily Sales}}$) and trigger proactive alerts when $DIR < \text{Supplier Lead Time}$.
- **Transparent Mathematical Replenishment**: Expose the complete statistical safety stock, lead-time demand, and target inventory calculation in the user interface.
- **Supplier Intelligence**: Multi-attribute ranking algorithm balancing lead-time urgency, purchase cost, reliability score, and return rate.
- **FEFO Expiry & Dead Stock Optimization**: Monitor shelf life, calculate potential unsold loss in ₹ INR, and recommend clearance markdowns or promotional bundles.
- **Natural Language Assistant**: Provide a zero-hallucination conversational interface connected to live database tools.
- **Human-In-The-Loop Governance**: Ensure all purchase orders require explicit shopkeeper confirmation (Approve, Modify, or Reject with recorded reason).

---

## 5. EXISTING SYSTEM VS. PROPOSED SYSTEM

| Parameter | Existing Retail Systems | Proposed Inventory Management AI |
|---|---|---|
| **System Paradigm** | Passive CRUD Ledger / Billing App | Autonomous Agentic AI Decision Engine |
| **Forecasting** | None or simple fixed percentage | Comparative ML (Moving Average, Linear Reg, Random Forest) |
| **Safety Stock** | Fixed manual threshold | Statistical dynamic safety buffer ($Z \times \sigma_D \times \sqrt{L}$) |
| **Reorder Guidance** | Opaque number or absent | Transparent formula breakdown with lead-time demand & MOQ |
| **Supplier Selection** | Single hardcoded supplier | Multi-attribute AI ranking (urgency vs. price vs. reliability) |
| **Shelf-Life Management**| Reactive disposal after expiry | Proactive FEFO markdown & unsold loss projection |
| **Regional Customization**| Generic Western formats | Indian Rupee (₹), Lakhs/Crores, GST CGST/SGST, Tamil localization |
| **Human Governance** | Manual or uncontrolled | Human-in-the-loop approval with continuous learning feedback |

---

## 6. SYSTEM ARCHITECTURE

The platform is architected around a three-tier modular architecture:

```
+-------------------------------------------------------------------------+
|                           PRESENTATION TIER                             |
|  - Modern Vanilla CSS Design System (Glassmorphism, Dark/Light Mode)    |
|  - Executive Dashboard, POS Terminal, Product Catalog, Inventory Ledger |
|  - AI Decision Cards, ML Forecasts, Supplier Scorecards, FEFO Expiry   |
|  - Canvas/SVG Interactive Charting Engine & Natural Language Assistant  |
+-------------------------------------------------------------------------+
                                   ▲
                                   │ REST APIs (JSON)
                                   ▼
+-------------------------------------------------------------------------+
|                            APPLICATION TIER                             |
|  - FastAPI High-Performance Asynchronous Python Framework               |
|  - RBAC Security (PBKDF2 Password Hashing, Signed Access Tokens)        |
|  - Core Services: Inventory Service, POS Billing, Purchases, Audits     |
|  - AGENTIC AI DECISION ENGINE:                                          |
|      * Observe -> Analyze -> Forecast -> Risk -> Reason -> Decide      |
|      * Machine Learning Forecaster (scikit-learn, NumPy, Pandas)        |
|      * Reorder & Safety Stock Engine                                    |
|      * Supplier Multi-Attribute Decision Reasoner                       |
|      * Natural Language AI Assistant Tool Registry                      |
|      * Continuous Feedback Learning Loop                                |
+-------------------------------------------------------------------------+
                                   ▲
                                   │ SQL (Foreign Keys, WAL Mode)
                                   ▼
+-------------------------------------------------------------------------+
|                               DATA TIER                                 |
|  - SQLite3 Relational Database (WAL Mode, High Concurrency)             |
|  - Tables: users, products, categories, suppliers, inventory, ledger,   |
|            sales, sale_items, purchases, batches, audits, ai_recom      |
+-------------------------------------------------------------------------+
```

---

## 7. AGENTIC AI WORKFLOW & ALGORITHMS

### 7.1 The Agentic Decision Loop

```
[OBSERVE]
   │ Scans stock balances, sales velocity, lead times, batch expiry dates
   ▼
[ANALYZE]
   │ Computes Average Daily Sales (ADS), sales volatility (σ_D), Days Remaining
   ▼
[FORECAST]
   │ Invokes ML models; selects model with lowest validation error; projects 1d/7d/30d
   ▼
[IDENTIFY RISK]
   │ Classifies risk: CRITICAL, REORDER NOW, REORDER SOON, SAFE, OVERSTOCK, DEAD STOCK
   ▼
[REASON]
   │ Ranks suppliers (urgency vs. price vs. reliability); computes statistical buffer
   ▼
[DECIDE & RECOMMEND]
   │ Generates transparent recommendation card with formula breakdown
   ▼
[HUMAN-IN-THE-LOOP]
   │ Shopkeeper reviews recommendation: [APPROVE] | [MODIFY] | [REJECT]
   ▼
[EXECUTE & FEEDBACK]
   │ On approval: auto-generates Purchase Order; records actual sales outcome to refine weights
```

### 7.2 Mathematical Formulations

1. **Days of Inventory Remaining ($DIR$)**:
   $$DIR = \frac{\text{Current Stock}}{\text{Average Daily Sales (ADS)}}$$

2. **Statistical Safety Stock ($SS$)**:
   For a 95% service level ($Z = 1.65$):
   $$SS = \max\left(\left\lceil Z \times \sigma_D \times \sqrt{L} \right\rceil, \text{Configured Buffer}\right)$$
   Where $\sigma_D$ is the historical standard deviation of daily sales and $L$ is supplier delivery lead time in days.

3. **Lead-Time Demand ($LTD$)**:
   $$LTD = \text{ADS} \times L$$

4. **Target Inventory Level ($T$)**:
   $$T = LTD + SS$$

5. **Recommended Reorder Quantity ($Q_{rec}$)**:
   $$Q_{raw} = T - \text{Current Stock}$$
   $$Q_{rec} = \max(Q_{raw}, \text{MOQ})$$

6. **Multi-Attribute Supplier Score ($S$)**:
   $$S = (W_{lead} \times S_{lead}) + (W_{rel} \times S_{rel}) + (W_{price} \times S_{price})$$
   - If stock is **CRITICAL**: $W_{lead} = 0.50, W_{rel} = 0.30, W_{price} = 0.20$ (Prioritizes fulfillment speed).
   - If stock is **SAFE / MONITOR**: $W_{price} = 0.50, W_{rel} = 0.30, W_{lead} = 0.20$ (Prioritizes unit cost savings).

---

## 8. DATABASE DESIGN

The relational schema is implemented in SQLite3 with foreign keys enabled, WAL journaling mode, and performance indexing:

1. **`users`**: RBAC credentials (Admin, Manager, Cashier) with PBKDF2 hash.
2. **`categories`**: Product taxonomy with English and Tamil names.
3. **`products`**: Master SKU table (barcode, dual names, unit, purchase price, selling price, MRP, GST rate, min/max stock, safety stock).
4. **`suppliers`**: Wholesale vendor master (contact, Tamil Nadu district, rating, reliability score, lead time, return rate).
5. **`supplier_products`**: Vendor catalog mappings with unit costs, MOQs, and lead times.
6. **`inventory`**: Real-time current stock and reserved stock balances.
7. **`inventory_transactions`**: Immutable audit ledger recording every quantity change with user, timestamp, transaction type, and reference number.
8. **`sales` & `sale_items`**: Retail customer invoices with CGST/SGST tax breakdown and payment methods.
9. **`purchases` & `purchase_items`**: Wholesale purchase orders and goods inward receipts.
10. **`product_batches`**: FEFO batch management with manufacturing and expiration dates.
11. **`stock_audits` & `stock_audit_items`**: Physical shelf count reconciliation with AI discrepancy diagnostics.
12. **`ai_recommendations`**: Stored agentic proposals, formula breakdowns, and human approval status.
13. **`ai_feedback_log`**: Historical post-recommendation error logging for continuous model refinement.

---

## 9. TESTING & VERIFICATION RESULTS

A comprehensive automated test suite of 13 unit and integration tests was implemented and executed:

```
test_agentic_loop_and_human_in_the_loop_approval (test_agent_and_ai) ... ok
test_feedback_loop_and_accuracy_tracking (test_agent_and_ai) ... ok
test_natural_language_assistant_factual_queries (test_agent_and_ai) ... ok
test_password_hashing_and_verification (test_auth_and_roles) ... ok
test_token_creation_and_signature_decoding (test_auth_and_roles) ... ok
test_forecast_generation_and_model_comparison (test_forecasting_models) ... ok
test_stock_transaction_and_audit_trail (test_inventory_ledger) ... ok
test_cart_preview_and_gst_split (test_pos_billing) ... ok
test_checkout_reduces_inventory (test_pos_billing) ... ok
test_customer_return_restores_inventory (test_pos_billing) ... ok
test_dead_stock_detection (test_reorder_and_suppliers) ... ok
test_fefo_expiry_evaluation (test_reorder_and_suppliers) ... ok
test_reorder_formula_breakdown (test_reorder_and_suppliers) ... ok

----------------------------------------------------------------------
Ran 13 tests in 5.136s
OK (100% Pass Rate)
```

---

## 10. ADVANTAGES & BUSINESS IMPACT

1. **Zero Stockouts on Critical Essentials**: Proactive lead-time comparison prevents stockouts before delivery windows breach.
2. **Capital Unlocking**: Detects dead stock and slow-moving items early, releasing locked-up working capital through clearance discounts.
3. **Transparent Decision Support**: Eliminates skepticism through transparent mathematical formulas and human-in-the-loop confirmation.
4. **GST & Regional Compliance**: Native support for CGST/SGST, thermal invoice printing, Indian Lakhs/Crores currency, and Tamil language.
5. **High Performance**: Sub-millisecond database queries, lightweight client-side Canvas charting, and zero heavy external framework overhead.

---

## 11. LIMITATIONS & FUTURE SCOPE

### Current Limitations
- External weather API feeds (e.g. monsoon rainfall impact on delivery) are modeled as calendar indicators rather than live satellite feeds.
- Offline-only desktop installation requires manual backup of the SQLite database file.

### Future Scope
- **Direct WhatsApp / SMS Purchase Orders**: Transmit approved purchase orders directly to Tamil Nadu wholesale suppliers via WhatsApp Business API.
- **Computer Vision Barcode & OCR**: Integrate camera-based invoice scanning to auto-inward supplier delivery bills.
- **Multi-Store Network Synchronization**: Expand the single-store architecture into a multi-branch warehouse distribution network across South India.

---

## 12. CONCLUSION

**Inventory Management AI** successfully demonstrates that modern Agentic Artificial Intelligence and Machine Learning can be practically, affordably, and transparently deployed to solve real-world retail inventory problems in India. By combining rigorous statistical inventory modeling with an intuitive, bilingual, and explainable interface, the system empowers small and medium-sized retail shopkeepers to optimize stock levels, prevent stockouts, eliminate dead capital, and run efficient, modern retail enterprises.

---

## 13. REFERENCES
1. Silver, E. A., Pyke, D. F., & Thomas, D. J. (2016). *Inventory and Production Management in Supply Chains*. CRC Press.
2. Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*. Springer.
3. Government of India, Ministry of Finance (2017). *Goods and Services Tax (GST) Architecture & Slabs*.
4. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach (4th Edition)*. Pearson.
5. Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research.
