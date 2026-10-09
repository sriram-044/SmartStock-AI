from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.database.db import get_db, transaction
from backend.auth.roles import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER
from backend.ai.tool_registry import BaseTool, ToolRegistry, ToolContext
from backend.ai.forecasting import get_product_forecast
from backend.ai.reorder_engine import ReorderEngine
from backend.ai.expiry_engine import evaluate_expiry_risks
from backend.ai.dead_stock_engine import analyze_dead_and_slow_stock
from backend.services.purchase_service import create_purchase_order, get_purchase_by_id
from backend.ai.feedback_loop import record_recommendation_outcome


# ==============================================================================
# 1. INVENTORY & PRODUCT TOOLS
# ==============================================================================

class QueryInventoryInput(BaseModel):
    query: Optional[str] = Field(None, description="Product name, Tamil name, or barcode substring")
    category_id: Optional[int] = Field(None, description="Category filter")
    low_stock_only: bool = Field(False, description="Filter for products at or below reorder level")
    limit: int = Field(20, ge=1, le=100)


class QueryInventoryTool(BaseTool):
    name = "get_inventory"
    description = "Retrieves live inventory stock, reorder levels, prices, and suppliers with optional search and filters."
    input_schema = QueryInventoryInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: QueryInventoryInput, context: ToolContext) -> List[Dict[str, Any]]:
        conn = get_db()
        try:
            sql = """
                SELECT p.id, p.barcode, p.name, p.tamil_name, p.unit, p.selling_price,
                       p.purchase_price, p.min_stock, p.max_stock, p.reorder_level, p.safety_stock,
                       i.current_stock, c.name as category_name, s.name as preferred_supplier_name,
                       s.avg_lead_time_days
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.is_active = 1
            """
            params: List[Any] = []
            if validated_input.query:
                q = f"%{validated_input.query.strip()}%"
                sql += " AND (p.name LIKE ? OR p.tamil_name LIKE ? OR p.barcode LIKE ?)"
                params.extend([q, q, q])
            if validated_input.category_id:
                sql += " AND p.category_id = ?"
                params.append(validated_input.category_id)
            if validated_input.low_stock_only:
                sql += " AND i.current_stock <= p.reorder_level"

            sql += " ORDER BY i.current_stock ASC LIMIT ?"
            params.append(validated_input.limit)

            cur = conn.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


class ProductDetailsInput(BaseModel):
    product_id: int = Field(..., description="Unique product ID")


class ProductDetailsTool(BaseTool):
    name = "get_product_details"
    description = "Fetches comprehensive product specifications, current stock, GST rate, cost, and preferred supplier."
    input_schema = ProductDetailsInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: ProductDetailsInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.*, i.current_stock, i.reserved_stock,
                       c.name as category_name, s.name as supplier_name,
                       s.avg_lead_time_days, s.reliability_score
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.id = ?
                """,
                (validated_input.product_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Product ID {validated_input.product_id} not found.")
            return dict(row)
        finally:
            conn.close()


# ==============================================================================
# 2. SALES HISTORY & ANALYTICS TOOLS
# ==============================================================================

class SalesHistoryInput(BaseModel):
    product_id: Optional[int] = Field(None, description="Specific product ID")
    days: int = Field(30, ge=1, le=180, description="History window in days")


class SalesHistoryTool(BaseTool):
    name = "get_sales_history"
    description = "Retrieves historical daily sales volume, transaction frequency, and revenue over N days."
    input_schema = SalesHistoryInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: SalesHistoryInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            sql = """
                SELECT DATE(s.created_at) as sale_date,
                       COALESCE(SUM(si.quantity), 0.0) as daily_units,
                       ROUND(COALESCE(SUM(si.total), 0.0), 2) as daily_revenue,
                       COUNT(DISTINCT s.id) as bills_count
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE DATE(s.created_at) >= DATE('now', ?)
            """
            params: List[Any] = [f"-{validated_input.days} days"]
            if validated_input.product_id:
                sql += " AND si.product_id = ?"
                params.append(validated_input.product_id)

            sql += " GROUP BY DATE(s.created_at) ORDER BY sale_date DESC"
            cur = conn.execute(sql, params)
            daily_rows = [dict(r) for r in cur.fetchall()]

            total_units = sum(r["daily_units"] for r in daily_rows)
            total_rev = sum(r["daily_revenue"] for r in daily_rows)
            avg_daily_units = round(total_units / max(len(daily_rows), 1), 2)

            return {
                "product_id": validated_input.product_id,
                "days_analyzed": validated_input.days,
                "days_with_sales": len(daily_rows),
                "total_units_sold": total_units,
                "total_revenue_inr": round(total_rev, 2),
                "avg_daily_units": avg_daily_units,
                "daily_trend": daily_rows[:15]
            }
        finally:
            conn.close()


class SalesAnalyticsInput(BaseModel):
    days: int = Field(30, ge=7, le=90)
    top_limit: int = Field(10, ge=1, le=30)


class SalesAnalyticsTool(BaseTool):
    name = "get_sales_analytics"
    description = "Provides high-level business metrics: revenue, gross margin, turnover, and top-selling SKUs."
    input_schema = SalesAnalyticsInput
    required_roles = [ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: SalesAnalyticsInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.id, p.name, p.tamil_name, p.unit,
                       COALESCE(SUM(si.quantity), 0) as units_sold,
                       ROUND(COALESCE(SUM(si.total), 0), 2) as revenue,
                       ROUND(COALESCE(SUM(si.quantity * (p.selling_price - p.purchase_price)), 0), 2) as gross_profit
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.created_at) >= DATE('now', ?)
                GROUP BY p.id
                ORDER BY revenue DESC
                LIMIT ?
                """,
                (f"-{validated_input.days} days", validated_input.top_limit)
            )
            top_products = [dict(r) for r in cur.fetchall()]
            total_rev = sum(p["revenue"] for p in top_products)
            total_profit = sum(p["gross_profit"] for p in top_products)

            return {
                "period_days": validated_input.days,
                "top_products_revenue_inr": round(total_rev, 2),
                "top_products_gross_profit_inr": round(total_profit, 2),
                "overall_margin_percent": round((total_profit / total_rev * 100), 1) if total_rev > 0 else 0.0,
                "top_selling_items": top_products
            }
        finally:
            conn.close()


# ==============================================================================
# 3. FORECASTING & REORDER ENGINES
# ==============================================================================

class ForecastDemandInput(BaseModel):
    product_id: int = Field(..., description="Product ID to forecast")


class ForecastDemandTool(BaseTool):
    name = "forecast_demand"
    description = "Runs multi-model ML demand forecasting (Moving Average, Linear Regression, Random Forest) and returns predictions."
    input_schema = ForecastDemandInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: ForecastDemandInput, context: ToolContext) -> Dict[str, Any]:
        return get_product_forecast(validated_input.product_id)


class StockoutRiskInput(BaseModel):
    product_id: int = Field(..., description="Product ID to evaluate")


class StockoutRiskTool(BaseTool):
    name = "calculate_stockout_risk"
    description = "Calculates days of inventory remaining, stockout risk level (CRITICAL, REORDER_NOW, REORDER_SOON, SAFE), and safety stock."
    input_schema = StockoutRiskInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: StockoutRiskInput, context: ToolContext) -> Dict[str, Any]:
        engine = ReorderEngine(validated_input.product_id)
        return engine.evaluate()


class ReorderQuantityInput(BaseModel):
    product_id: int = Field(..., description="Product ID")
    days_horizon: int = Field(7, ge=1, le=30, description="Planning horizon in days")


class ReorderQuantityTool(BaseTool):
    name = "calculate_reorder_quantity"
    description = "Calculates exact replenishment quantity adhering to safety stock, lead time demand, and supplier MOQ."
    input_schema = ReorderQuantityInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: ReorderQuantityInput, context: ToolContext) -> Dict[str, Any]:
        engine = ReorderEngine(validated_input.product_id)
        eval_res = engine.evaluate()
        return {
            "product_id": validated_input.product_id,
            "product_name": eval_res.get("product_name"),
            "current_stock": eval_res.get("current_stock"),
            "recommended_qty": eval_res.get("recommended_qty"),
            "risk_level": eval_res.get("risk_level"),
            "status_label": eval_res.get("status_label"),
            "best_supplier": eval_res.get("best_supplier"),
            "formula_breakdown": eval_res.get("formula_breakdown")
        }


# ==============================================================================
# 4. EXPIRY & DEAD STOCK TOOLS
# ==============================================================================

class ExpiringProductsInput(BaseModel):
    days_window: int = Field(30, ge=7, le=120, description="Expiry lookahead window in days")


class ExpiringProductsTool(BaseTool):
    name = "identify_expiring_products"
    description = "Evaluates FEFO product batches expiring soon, calculates potential rupee loss, and suggests markdown rotation."
    input_schema = ExpiringProductsInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: ExpiringProductsInput, context: ToolContext) -> List[Dict[str, Any]]:
        return evaluate_expiry_risks(days_window=validated_input.days_window)


class DeadStockInput(BaseModel):
    days_threshold: int = Field(45, ge=14, le=180, description="Days with zero sales to classify as dead stock")


class DeadStockTool(BaseTool):
    name = "identify_dead_stock"
    description = "Detects dead and slow-moving inventory, calculates blocked working capital, and highlights capital recovery opportunities."
    input_schema = DeadStockInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: DeadStockInput, context: ToolContext) -> Dict[str, Any]:
        items = analyze_dead_and_slow_stock(days_threshold=validated_input.days_threshold)
        total_blocked = sum(it.get("blocked_capital", 0.0) for it in items)
        return {
            "threshold_days": validated_input.days_threshold,
            "total_dead_stock_items": len(items),
            "total_blocked_capital_inr": round(total_blocked, 2),
            "items": items[:15]
        }


# ==============================================================================
# 5. SUPPLIER INTELLIGENCE TOOLS
# ==============================================================================

class SupplierOptionsInput(BaseModel):
    product_id: int = Field(..., description="Product ID")


class SupplierOptionsTool(BaseTool):
    name = "get_supplier_options"
    description = "Lists all registered wholesale suppliers offering a product with quoted prices, MOQ, lead times, and reliability ratings."
    input_schema = SupplierOptionsInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: SupplierOptionsInput, context: ToolContext) -> List[Dict[str, Any]]:
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT s.id as supplier_id, s.name as supplier_name, s.district, s.phone,
                       s.rating, s.reliability_score, s.avg_lead_time_days, s.return_rate,
                       sp.supplier_price, sp.moq, sp.delivery_time_days
                FROM supplier_products sp
                JOIN suppliers s ON sp.supplier_id = s.id
                WHERE sp.product_id = ?
                ORDER BY sp.supplier_price ASC, s.reliability_score DESC
                """,
                (validated_input.product_id,)
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


class CompareSuppliersInput(BaseModel):
    product_id: int = Field(..., description="Product ID")
    urgency_days: Optional[int] = Field(None, description="Max allowed delivery days")


class CompareSuppliersTool(BaseTool):
    name = "compare_suppliers"
    description = "Compares supplier options, evaluating trade-offs between wholesale purchase price, lead time, and vendor reliability."
    input_schema = CompareSuppliersInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: CompareSuppliersInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT sp.supplier_id, s.name as supplier_name, sp.supplier_price,
                       sp.moq, sp.delivery_time_days, s.reliability_score, s.rating
                FROM supplier_products sp
                JOIN suppliers s ON sp.supplier_id = s.id
                WHERE sp.product_id = ?
                ORDER BY sp.supplier_price ASC
                """,
                (validated_input.product_id,)
            )
            options = [dict(r) for r in cur.fetchall()]
            if not options:
                return {"product_id": validated_input.product_id, "options": [], "recommended": None}

            cheapest = min(options, key=lambda x: x["supplier_price"])
            fastest = min(options, key=lambda x: x["delivery_time_days"])
            most_reliable = max(options, key=lambda x: x["reliability_score"])

            # Recommended choice balancing cost and reliability
            if validated_input.urgency_days is not None:
                eligible = [o for o in options if o["delivery_time_days"] <= validated_input.urgency_days]
                recommended = min(eligible, key=lambda x: x["supplier_price"]) if eligible else fastest
            else:
                recommended = cheapest if cheapest["reliability_score"] >= 90.0 else most_reliable

            return {
                "product_id": validated_input.product_id,
                "all_options": options,
                "cheapest_option": cheapest,
                "fastest_option": fastest,
                "most_reliable_option": most_reliable,
                "recommended_option": recommended
            }
        finally:
            conn.close()


# ==============================================================================
# 6. PROCUREMENT, BUDGET & PURCHASE ORDER TOOLS
# ==============================================================================

class BudgetItem(BaseModel):
    product_id: int
    quantity: float
    unit_cost: float
    gst_rate: float = 5.0


class CalculatePurchaseBudgetInput(BaseModel):
    items: List[BudgetItem] = Field(..., description="Proposed items to purchase")
    budget_limit_inr: Optional[float] = Field(None, description="Spending budget in INR")


class CalculatePurchaseBudgetTool(BaseTool):
    name = "calculate_purchase_budget"
    description = "Calculates total cost, GST breakdown, and verifies whether the purchase satisfies a budget constraint."
    input_schema = CalculatePurchaseBudgetInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: CalculatePurchaseBudgetInput, context: ToolContext) -> Dict[str, Any]:
        subtotal = 0.0
        gst_total = 0.0

        for it in validated_input.items:
            line_cost = round(it.quantity * it.unit_cost, 2)
            line_gst = round(line_cost * (it.gst_rate / 100.0), 2)
            subtotal += line_cost
            gst_total += line_gst

        total_amount = round(subtotal + gst_total, 2)
        budget = validated_input.budget_limit_inr

        is_within_budget = True
        budget_variance = 0.0
        if budget is not None:
            is_within_budget = total_amount <= budget
            budget_variance = round(budget - total_amount, 2)

        return {
            "item_count": len(validated_input.items),
            "subtotal_inr": round(subtotal, 2),
            "gst_amount_inr": round(gst_total, 2),
            "total_amount_inr": total_amount,
            "budget_limit_inr": budget,
            "is_within_budget": is_within_budget,
            "budget_variance_inr": budget_variance
        }


class PurchaseItemDraft(BaseModel):
    product_id: int
    quantity: float
    unit_cost: float
    gst_rate: Optional[float] = 5.0


class CreateDraftPOInput(BaseModel):
    supplier_id: int
    items: List[PurchaseItemDraft]
    expected_delivery: Optional[str] = None
    business_justification: Optional[str] = None


class CreateDraftPOTool(BaseTool):
    name = "create_purchase_order_draft"
    description = "Generates a non-binding draft Purchase Order proposal. Does NOT submit the order or spend money."
    input_schema = CreateDraftPOInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]
    is_consequential = False

    def run(self, validated_input: CreateDraftPOInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            # Verify supplier exists
            sup_cur = conn.execute("SELECT id, name, phone, avg_lead_time_days FROM suppliers WHERE id = ?", (validated_input.supplier_id,))
            supplier = sup_cur.fetchone()
            if not supplier:
                raise ValueError(f"Supplier ID {validated_input.supplier_id} not found.")

            # Validate products
            draft_items = []
            subtotal = 0.0
            gst_total = 0.0

            for it in validated_input.items:
                p_cur = conn.execute("SELECT id, name, unit FROM products WHERE id = ?", (it.product_id,))
                prod = p_cur.fetchone()
                if not prod:
                    raise ValueError(f"Product ID {it.product_id} not found.")

                line_cost = round(it.quantity * it.unit_cost, 2)
                line_gst = round(line_cost * ((it.gst_rate or 5.0) / 100.0), 2)
                subtotal += line_cost
                gst_total += line_gst

                draft_items.append({
                    "product_id": it.product_id,
                    "product_name": prod["name"],
                    "unit": prod["unit"],
                    "quantity": it.quantity,
                    "unit_cost": it.unit_cost,
                    "gst_rate": it.gst_rate or 5.0,
                    "line_cost": line_cost,
                    "line_gst": line_gst
                })

            total_amount = round(subtotal + gst_total, 2)
            draft_id = f"DRAFT-PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return {
                "draft_id": draft_id,
                "supplier_id": validated_input.supplier_id,
                "supplier_name": supplier["name"],
                "supplier_lead_time": supplier["avg_lead_time_days"],
                "items": draft_items,
                "subtotal_inr": round(subtotal, 2),
                "gst_amount_inr": round(gst_total, 2),
                "total_amount_inr": total_amount,
                "justification": validated_input.business_justification or "Automated inventory replenishment draft",
                "status": "DRAFT",
                "requires_approval": True
            }
        finally:
            conn.close()


class ValidatePOInput(BaseModel):
    supplier_id: int
    items: List[PurchaseItemDraft]
    budget_limit_inr: Optional[float] = None


class ValidatePOTool(BaseTool):
    name = "validate_purchase_order"
    description = "Checks that a proposed purchase order meets all constraints (active supplier, valid products, positive quantities, MOQ, budget)."
    input_schema = ValidatePOInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: ValidatePOInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            errors = []
            warnings = []

            # Check supplier
            sup_cur = conn.execute("SELECT id, name FROM suppliers WHERE id = ?", (validated_input.supplier_id,))
            supplier = sup_cur.fetchone()
            if not supplier:
                errors.append(f"Supplier ID {validated_input.supplier_id} does not exist.")

            if not validated_input.items:
                errors.append("Purchase order has no items.")

            total_cost = 0.0
            for idx, it in enumerate(validated_input.items):
                if it.quantity <= 0:
                    errors.append(f"Item #{idx+1} (Product {it.product_id}) quantity must be greater than zero.")
                if it.unit_cost <= 0:
                    errors.append(f"Item #{idx+1} (Product {it.product_id}) unit cost must be greater than zero.")

                p_cur = conn.execute("SELECT id, name, is_active FROM products WHERE id = ?", (it.product_id,))
                prod = p_cur.fetchone()
                if not prod:
                    errors.append(f"Product ID {it.product_id} does not exist.")
                elif not prod["is_active"]:
                    errors.append(f"Product '{prod['name']}' is marked inactive.")

                # Check MOQ if supplier catalog exists
                moq_cur = conn.execute(
                    "SELECT moq FROM supplier_products WHERE supplier_id = ? AND product_id = ?",
                    (validated_input.supplier_id, it.product_id)
                )
                moq_row = moq_cur.fetchone()
                if moq_row and it.quantity < moq_row["moq"]:
                    warnings.append(f"Product {it.product_id} quantity ({it.quantity}) is below supplier MOQ ({moq_row['moq']}).")

                line_cost = it.quantity * it.unit_cost * (1 + (it.gst_rate or 5.0) / 100.0)
                total_cost += line_cost

            # Check budget
            if validated_input.budget_limit_inr is not None and total_cost > validated_input.budget_limit_inr:
                errors.append(
                    f"Total cost ₹{round(total_cost, 2):,.2f} exceeds allocated budget limit ₹{validated_input.budget_limit_inr:,.2f}."
                )

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "estimated_total_cost_inr": round(total_cost, 2)
            }
        finally:
            conn.close()


class SubmitApprovedPOInput(BaseModel):
    supplier_id: int
    items: List[PurchaseItemDraft]
    invoice_number: Optional[str] = None
    approval_token: Optional[str] = Field(None, description="Approval verification token or confirmation flag")


class SubmitApprovedPOTool(BaseTool):
    name = "submit_approved_purchase_order"
    description = "Executes the creation of an official Purchase Order in the database. REQUIRES MANAGER OR ADMIN ROLE and valid approval."
    input_schema = SubmitApprovedPOInput
    required_roles = [ROLE_MANAGER, ROLE_ADMIN]
    is_consequential = True
    requires_approval = True

    def run(self, validated_input: SubmitApprovedPOInput, context: ToolContext) -> Dict[str, Any]:
        # Enforce that caller cannot be cashier
        if context.user_role.lower() not in [ROLE_ADMIN, ROLE_MANAGER]:
            raise PermissionError("Only Store Managers or Admins can submit approved purchase orders.")

        po_data = {
            "supplier_id": validated_input.supplier_id,
            "invoice_number": validated_input.invoice_number or f"AI-AGENT-{datetime.now().strftime('%Y%m%d%H%M')}",
            "items": [it.model_dump() for it in validated_input.items]
        }

        created_po = create_purchase_order(po_data, user_id=context.user_id)
        return {
            "status": "ORDERED",
            "po_number": created_po["po_number"],
            "total_amount": created_po["total_amount"],
            "supplier_id": validated_input.supplier_id,
            "item_count": len(validated_input.items),
            "submitted_by_user_id": context.user_id,
            "submitted_at": datetime.now().isoformat()
        }


class VerifyPOInput(BaseModel):
    po_number: Optional[str] = None
    purchase_id: Optional[int] = None


class VerifyPOTool(BaseTool):
    name = "verify_purchase_order"
    description = "Verifies that a purchase order exists in the database, verifying item counts and status."
    input_schema = VerifyPOInput
    required_roles = [ROLE_CASHIER, ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: VerifyPOInput, context: ToolContext) -> Dict[str, Any]:
        conn = get_db()
        try:
            if validated_input.purchase_id:
                po = get_purchase_by_id(validated_input.purchase_id)
            elif validated_input.po_number:
                cur = conn.execute("SELECT id FROM purchases WHERE po_number = ?", (validated_input.po_number,))
                row = cur.fetchone()
                po = get_purchase_by_id(row["id"]) if row else None
            else:
                raise ValueError("Must provide either po_number or purchase_id.")

            if not po:
                return {
                    "verified": False,
                    "message": "Purchase order does not exist in the database."
                }

            return {
                "verified": True,
                "po_number": po["po_number"],
                "status": po["status"],
                "supplier_name": po.get("supplier_name"),
                "total_amount": po["total_amount"],
                "items_count": len(po.get("items", [])),
                "created_at": po.get("created_at")
            }
        finally:
            conn.close()


class RecordFeedbackInput(BaseModel):
    recommendation_id: int
    actual_sales_observed: float
    notes: Optional[str] = None


class RecordFeedbackTool(BaseTool):
    name = "record_recommendation_feedback"
    description = "Logs actual sales outcome vs predicted demand to compute forecast error and refine models."
    input_schema = RecordFeedbackInput
    required_roles = [ROLE_MANAGER, ROLE_ADMIN]

    def run(self, validated_input: RecordFeedbackInput, context: ToolContext) -> Dict[str, Any]:
        return record_recommendation_outcome(
            recommendation_id=validated_input.recommendation_id,
            actual_sales_observed=validated_input.actual_sales_observed,
            outcome_notes=validated_input.notes or ""
        )


# ==============================================================================
# TOOL REGISTRATION HELPER
# ==============================================================================

def register_all_tools() -> None:
    """Instantiates and registers all system tools in the ToolRegistry."""
    tools: List[BaseTool] = [
        QueryInventoryTool(),
        ProductDetailsTool(),
        SalesHistoryTool(),
        SalesAnalyticsTool(),
        ForecastDemandTool(),
        StockoutRiskTool(),
        ReorderQuantityTool(),
        ExpiringProductsTool(),
        DeadStockTool(),
        SupplierOptionsTool(),
        CompareSuppliersTool(),
        CalculatePurchaseBudgetTool(),
        CreateDraftPOTool(),
        ValidatePOTool(),
        SubmitApprovedPOTool(),
        VerifyPOTool(),
        RecordFeedbackTool(),
    ]
    for t in tools:
        ToolRegistry.register(t)


# Automatically register on import
register_all_tools()
