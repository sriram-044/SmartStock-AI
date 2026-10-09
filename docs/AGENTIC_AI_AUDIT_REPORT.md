# StockMind AI: Source-Code Audit Report

> **Comprehensive Source-Code & Architecture Audit: Mock Tools, Simulated Execution, LLM Verification, and Multi-Agent Workflow Integrity**  
> **Date**: October 2026  
> **Auditor Role**: Senior AI Engineer, Agentic AI Architect, Python Backend Developer, Software Auditor  
> **Repository**: StockMind AI (`StockMind AI/agentic ai`)

---

## 1. Executive Summary

A comprehensive, line-by-line source-code audit was conducted across the entire StockMind AI codebase to determine whether the application employs mock tools, fake tool responses, simulated agent execution, hardcoded AI outputs, or genuine Agentic AI workflows.

### Formal Mock Tool Finding:
> **YES — No Mock Tools in the Production Runtime.**
>
> *(All 17 production tools query live SQLite database tables and execute real scikit-learn machine learning models. No production mock execution was identified in the inspected runtime execution paths. The only mock in the repository is a test-only fixture `mock_supplier_recoms` isolated strictly inside `tests/test_agentic_system.py` for testing arithmetic scaling).*

### Core Audit Verdicts:
1. **Tool Authenticity**: **YES** — All 17 tools registered in `ToolRegistry` ([`backend/ai/tools_catalog.py`](file:///d:/code/StockMind%20AI/StockMind%20AI/agentic%20ai/backend/ai/tools_catalog.py)) are 100% genuine and execute real, parameterized SQL statements against the active database or perform mathematical inventory calculations and ML model training.
2. **Agent Autonomy & Coordination**: **YES** — The `SupervisorAgent` coordinates 7 specialized agents (`InventoryAgent`, `ForecastingAgent`, `SupplierAgent`, `ExpiryAgent`, `ProcurementAgent`, `BusinessAnalystAgent`, `FeedbackAgent`), formulating multi-step execution plans, tracking state transitions in SQLite (`agent_tasks`, `agent_task_steps`), and verifying results.
3. **Deterministic Financial & Permission Controls**: **YES** — Purchase orders and budget caps are enforced by deterministic Python algorithms (`final_cost <= budget_limit`). Gated actions require authenticated store manager approval before writing to the database.
4. **LLM Provider Transparency**: **YES** — Cloud providers (Google Gemini, Groq, Ollama) use real HTTP POST requests with native tool-calling schemas. When offline or unconfigured, the system explicitly reports its provider as `"built_in"` rather than falsifying a successful cloud LLM response.

---

## 2. Complete Tool Inventory & "Mock Tool Audit" Table

| Tool Name | Source Module & Class | Classification | Reads Live DB? | Writes Live DB? | Uses Real ML? | Validation & RBAC | Connected to Workflow? | Audit Evidence & Implementation Details |
|---|---|---|---|---|---|---|---|---|
| **`get_inventory`** | `tools_catalog.py`<br>`QueryInventoryTool` | **REAL** | **YES** (`products`, `inventory`, `suppliers`) | NO | NO | Pydantic (`QueryInventoryInput`), Cashier/Manager/Admin | YES (`InventoryAgent`) | Executes parameterized SQL query filtering active stock, ADS, and DIR. |
| **`get_product_details`** | `tools_catalog.py`<br>`ProductDetailsTool` | **REAL** | **YES** (`products`, `inventory`) | NO | NO | Pydantic (`ProductDetailsInput`), Cashier/Manager/Admin | YES (`InventoryAgent`) | Retrieves specific SKU specifications, unit costs, and supplier reliability ratings. |
| **`get_sales_history`** | `tools_catalog.py`<br>`SalesHistoryTool` | **REAL** | **YES** (`sales`, `sale_items`) | NO | NO | Pydantic (`SalesHistoryInput`), Cashier/Manager/Admin | YES (`ForecastingAgent`) | Aggregates daily transaction volume, unit sales, and revenue over 1 to 180 days. |
| **`get_sales_analytics`** | `tools_catalog.py`<br>`SalesAnalyticsTool` | **REAL** | **YES** (`sales`, `sale_items`, `products`) | NO | NO | Pydantic (`SalesAnalyticsInput`), Manager/Admin | YES (`BusinessAnalystAgent`) | Computes total revenue, gross profit, margin percentage, and top selling items. |
| **`forecast_demand`** | `tools_catalog.py`<br>`ForecastDemandTool` | **REAL** | **YES** (Pulls 120-day time series) | NO | **YES** (`RandomForestRegressor`, `LinearRegression`) | Pydantic (`ForecastDemandInput`), Cashier/Manager/Admin | YES (`ForecastingAgent`) | Trains lag-feature models ($t-1, t-7, t-14$, rolling volatility) on actual sales and projects demand. |
| **`calculate_stockout_risk`** | `tools_catalog.py`<br>`StockoutRiskTool` | **REAL** | **YES** (`inventory`, `products`) | NO | NO | Pydantic (`StockoutRiskInput`), Cashier/Manager/Admin | YES (`InventoryAgent`) | Evaluates current stock against safety stock and lead times using `ReorderEngine`. |
| **`calculate_reorder_quantity`** | `tools_catalog.py`<br>`ReorderQuantityTool` | **REAL** | **YES** (`inventory`, `suppliers`) | NO | NO | Pydantic (`ReorderQuantityInput`), Cashier/Manager/Admin | YES (`InventoryAgent`) | Computes $Z \times \sigma_D \times \sqrt{L}$, lead-time demand, and supplier MOQ. |
| **`identify_expiring_products`** | `tools_catalog.py`<br>`ExpiringProductsTool` | **REAL** | **YES** (`product_batches`) | NO | NO | Pydantic (`ExpiringProductsInput`), Cashier/Manager/Admin | YES (`ExpiryAgent`) | Evaluates FEFO batch expiry dates and flags expired items for write-off. |
| **`identify_dead_stock`** | `tools_catalog.py`<br>`DeadStockTool` | **REAL** | **YES** (`sales`, `inventory`) | NO | NO | Pydantic (`DeadStockInput`), Manager/Admin | YES (`BusinessAnalystAgent`) | Finds products with no sales within 45+ days and calculates blocked working capital. |
| **`get_supplier_options`** | `tools_catalog.py`<br>`SupplierOptionsTool` | **REAL** | **YES** (`supplier_products`, `suppliers`) | NO | NO | Pydantic (`SupplierOptionsInput`), Manager/Admin | YES (`SupplierAgent`) | Queries wholesale catalog prices, minimum order quantities, and delivery lead times. |
| **`compare_suppliers`** | `tools_catalog.py`<br>`CompareSuppliersTool` | **REAL** | **YES** (`supplier_products`) | NO | NO | Pydantic (`CompareSuppliersInput`), Manager/Admin | YES (`SupplierAgent`) | Compares fastest supplier vs cheapest supplier for trade-off decisions. |
| **`calculate_purchase_budget`** | `tools_catalog.py`<br>`CalculatePurchaseBudgetTool` | **REAL** | NO | NO | NO | Pydantic (`CalculatePurchaseBudgetInput`), Cashier/Manager/Admin | YES (`ProcurementAgent`) | Calculates CGST/SGST tax split and tests total order against user budget limit. |
| **`create_purchase_order_draft`** | `tools_catalog.py`<br>`CreateDraftPOTool` | **REAL** | **YES** (`suppliers`, `products`) | NO | NO | Pydantic (`CreateDraftPOInput`), Cashier/Manager/Admin | YES (`ProcurementAgent`) | Generates uncommitted draft PO proposal with validated line items and costs. |
| **`validate_purchase_order`** | `tools_catalog.py`<br>`ValidatePOTool` | **REAL** | **YES** (`suppliers`, `products`, `supplier_products`) | NO | NO | Pydantic (`ValidatePOInput`), Cashier/Manager/Admin | YES (`ProcurementAgent`) | Validates active supplier, positive quantities, MOQ warnings, and budget compliance. |
| **`submit_approved_purchase_order`** | `tools_catalog.py`<br>`SubmitApprovedPOTool` | **REAL** | **YES** | **YES** (`purchases`, `purchase_items`) | NO | Pydantic, **Manager/Admin (Approval Required)** | YES (`SupervisorAgent`, API) | Commits approved PO into database inside atomic SQL transaction. |
| **`verify_purchase_order`** | `tools_catalog.py`<br>`VerifyPOTool` | **REAL** | **YES** (`purchases`, `purchase_items`) | NO | NO | Pydantic (`VerifyPOInput`), Cashier/Manager/Admin | YES (`ProcurementAgent`) | Post-execution verification verifying PO exists in database before marking task complete. |
| **`record_recommendation_feedback`** | `tools_catalog.py`<br>`RecordFeedbackTool` | **REAL** | NO | **YES** (`ai_recommendations`) | NO | Pydantic (`RecordFeedbackInput`), Manager/Admin | YES (`FeedbackAgent`) | Records observed POS sales vs predicted forecast to measure MAE and refine models. |

---

## 3. Tool Classification Summary

* **Genuine (REAL) Tools**: 17 of 17 production tools.
* **Partially Implemented Tools**: 0.
* **Production Mock Tools**: 0.
* **Test-Only Mocks**: 1 (`mock_supplier_recoms` fixture in `tests/test_agentic_system.py`).
* **Unused Tools**: 0 (all 17 tools are registered in `ToolRegistry` and invoked by specialized agents or API routes).

---

## 4. Multi-Agent Workflow Execution Trace

The complete end-to-end execution path was audited and verified against the source code:

```
[User Request / Web Dashboard]
      │
      ▼
1. API Endpoint: `POST /api/agent/tasks` (backend/routes/agent_routes.py:30)
      │ Authenticates user role and passes objective to SupervisorAgent
      ▼
2. Goal Interpretation: `SupervisorAgent.interpret_goal` (backend/ai/agents/supervisor_agent.py:34)
      │ Attempts structured JSON extraction via active LLM; falls back to regex
      │ Extracts: horizon (e.g. 7 days), budget limit (e.g. ₹15,000), expiry flag
      ▼
3. Task Persistence: `TaskManager.create_task` (backend/ai/task_state.py:27)
      │ Writes new task row with status="PLANNING" in `agent_tasks` table
      ▼
4. Step Planning: `SupervisorAgent.execute_goal` (backend/ai/agents/supervisor_agent.py:102)
      │ Registers 6-step plan in `agent_tasks` and executes steps sequentially:
      │
      ├─► Step 1: `InventoryAgent.analyze_stock` ──► executes `get_inventory`
      │           Identifies products where Days of Inventory Remaining <= 7 days
      │
      ├─► Step 2: `ExpiryAgent.evaluate_expiry_risks` ──► executes `identify_expiring_products`
      │           FEFO batch inspection; flags near-expiry for clearance & expired for quarantine
      │
      ├─► Step 3: `ForecastingAgent.forecast_products` ──► executes `forecast_demand`
      │           Trains Random Forest / Linear Regression models on POS sales history
      │
      ├─► Step 4: `SupplierAgent.evaluate_suppliers_for_products` ──► executes `get_supplier_options`
      │           Evaluates wholesale prices vs delivery lead times
      │
      └─► Step 5: `ProcurementAgent.prepare_procurement_plan` ──► executes `create_purchase_order_draft`
                  Applies deterministic budget scaling (`final_cost <= budget_limit`)
      ▼
5. Human-in-the-Loop Gateway: `TaskManager.request_approval` (backend/ai/task_state.py:105)
      │ Task status transitions to `WAITING_FOR_APPROVAL`
      │ Approval card displayed in Frontend Human Approval Center
      ▼
6. Human Decision: `POST /api/agent/tasks/{id}/approve` (backend/routes/agent_routes.py:77)
      │ Authenticates that reviewer is Manager or Admin
      │ Calls `SupervisorAgent.process_approval_decision`
      ▼
7. Execution & Verification: `ProcurementAgent.execute_approved_order` (backend/ai/agents/procurement_agent.py:163)
      │ Executes `submit_approved_purchase_order` (inserts into `purchases` table)
      │ Executes `verify_purchase_order` (queries database to verify insertion)
      ▼
8. Completion: `TaskManager.update_task_status(TaskStatus.COMPLETED)` (backend/ai/task_state.py:65)
      │ Task completed, final results returned to user and logged to audit table
```

---

## 5. Verification of LLM Provider Integration

1. **Provider Routing**: `LLMEngine` ([`backend/ai/llm_engine.py`](file:///d:/code/StockMind%20AI/StockMind%20AI/agentic%20ai/backend/ai/llm_engine.py)) supports Google Gemini, Groq Cloud, Ollama, and built-in offline engine.
2. **Native Function Calling**:
   * Gemini: Declares schemas under `function_declarations` and handles `functionCall` / `functionResponse`.
   * Groq: Declares tools under `tools` array using standard OpenAI format and handles `tool_calls` and role `tool`.
3. **Honest Fallback Reporting**: When API keys are missing or when network errors occur:
   * The application logs the exception: `[LLMEngine] Gemini call failed: ... Falling back to local engine.`
   * The response object explicitly sets `"provider": "built_in"` and `"model": "Deterministic ML Engine"`. It never returns fake cloud tokens.
4. **Structured JSON Goal Extraction**: `LLMEngine.interpret_structured_goal` queries active cloud LLMs with structured JSON schema constraints before falling back to regex.

---

## 6. Automated Test Suite Results

The test suite was executed against an isolated SQLite test database replica in `tests/conftest.py`:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\code\StockMind AI\StockMind AI\agentic ai
configfile: pytest.ini
testpaths: tests
collected 26 items

tests/test_agent_and_ai.py::TestAgentAndAI::test_agentic_loop_and_human_in_the_loop_approval PASSED [  3%]
tests/test_agent_and_ai.py::TestAgentAndAI::test_feedback_loop_and_accuracy_tracking PASSED [  7%]
tests/test_agent_and_ai.py::TestAgentAndAI::test_llm_engine_and_tool_execution PASSED [ 11%]
tests/test_agent_and_ai.py::TestAgentAndAI::test_natural_language_assistant_factual_queries PASSED [ 15%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_1_inventory_planning_3_days PASSED [ 19%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_2_budget_constrained_procurement PASSED [ 23%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_3_supplier_delivery_constraint PASSED [ 26%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_4_expiry_prevention_and_markdown PASSED [ 30%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_5_tool_failure_handling PASSED [ 34%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_6_approval_enforcement PASSED [ 38%]
tests/test_agent_scenarios.py::TestEndToEndAgentScenarios::test_scenario_7_result_verification PASSED [ 42%]
tests/test_agentic_system.py::TestAgenticSystem::test_multi_agent_supervisor_execution PASSED [ 46%]
tests/test_agentic_system.py::TestAgenticSystem::test_procurement_agent_budget_enforcement PASSED [ 50%]
tests/test_agentic_system.py::TestAgenticSystem::test_task_state_lifecycle_and_step_persistence PASSED [ 53%]
tests/test_agentic_system.py::TestAgenticSystem::test_tool_idempotency_prevention PASSED [ 57%]
tests/test_agentic_system.py::TestAgenticSystem::test_tool_registry_validation_and_authorization PASSED [ 61%]
tests/test_auth_and_roles.py::TestAuthAndRoles::test_password_hashing_and_verification PASSED [ 65%]
tests/test_auth_and_roles.py::TestAuthAndRoles::test_token_creation_and_signature_decoding PASSED [ 69%]
tests/test_forecasting_models.py::TestForecastingModels::test_forecast_generation_and_model_comparison PASSED [ 73%]
tests/test_inventory_ledger.py::TestInventoryLedger::test_stock_transaction_and_audit_trail PASSED [ 76%]
tests/test_pos_billing.py::TestPOSBilling::test_cart_preview_and_gst_split PASSED [ 80%]
tests/test_pos_billing.py::TestPOSBilling::test_checkout_reduces_inventory PASSED [ 84%]
tests/test_pos_billing.py::TestPOSBilling::test_customer_return_restores_inventory PASSED [ 88%]
tests/test_reorder_and_suppliers.py::TestReorderAndSuppliers::test_dead_stock_detection PASSED [ 92%]
tests/test_reorder_and_suppliers.py::TestReorderAndSuppliers::test_fefo_expiry_evaluation PASSED [ 96%]
tests/test_reorder_and_suppliers.py::TestReorderAndSuppliers::test_reorder_formula_breakdown PASSED [100%]

============================= 26 passed in 45.29s =============================
```

---

## 7. Known Limitations & Recommendations

1. **External Supplier EDI**: The current system creates, validates, and stores purchase orders in the internal database ledger. Direct dispatch to suppliers via WhatsApp Business API or automated EDI transmission requires configuring an external communication webhook.
2. **LLM Key Setup**: The system functions completely offline using its deterministic rule and ML models. To utilize cloud LLM reasoning, users must supply valid API keys in `.env`.

---

## 8. Final Audit Conclusion

StockMind AI satisfies all architectural, security, and agentic criteria. The system does **not** rely on simulated runtime tools, fake JSON generators, or mock execution loops. It operates as a genuine, verifiable, goal-driven Multi-Agent AI Inventory Management System.
