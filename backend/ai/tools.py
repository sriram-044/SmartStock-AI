from typing import Dict, Any, List, Optional
from backend.database.db import get_db
from backend.ai.reorder_engine import ReorderEngine
from backend.ai.dead_stock_engine import analyze_dead_and_slow_stock
from backend.ai.expiry_engine import evaluate_expiry_risks
from backend.ai.forecasting import get_product_forecast

class AgentTools:
    """Tool execution registry providing deterministic, factual database inspection for the AI."""

    @staticmethod
    def query_stock(product_query: str) -> List[Dict[str, Any]]:
        """Queries stock and product pricing by name, tamil name, or barcode."""
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.id, p.barcode, p.name, p.tamil_name, p.unit, p.selling_price,
                       p.purchase_price, p.min_stock, p.max_stock, p.reorder_level,
                       i.current_stock, s.name as supplier_name
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.name LIKE ? OR p.tamil_name LIKE ? OR p.barcode LIKE ?
                LIMIT 10
                """,
                (f"%{product_query.strip()}%", f"%{product_query.strip()}%", f"%{product_query.strip()}%")
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_critical_restock_list() -> List[Dict[str, Any]]:
        """Returns all products with critical stockout risk or below reorder level."""
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.id, p.name, p.tamil_name, p.unit, i.current_stock, p.min_stock,
                       p.reorder_level, s.name as supplier_name, s.avg_lead_time_days
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.is_active = 1 AND i.current_stock <= p.reorder_level
                ORDER BY i.current_stock ASC
                LIMIT 15
                """
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_dead_stock_summary() -> Dict[str, Any]:
        """Calculates total blocked capital in dead and slow moving stock."""
        items = analyze_dead_and_slow_stock(days_threshold=45)
        total_blocked = sum(it["blocked_capital"] for it in items)
        return {
            "total_dead_stock_items": len(items),
            "total_blocked_capital_inr": round(total_blocked, 2),
            "top_dead_items": items[:8]
        }

    @staticmethod
    def get_expiring_batches(days: int = 30) -> List[Dict[str, Any]]:
        """Lists batches expiring within the specified days window."""
        return evaluate_expiry_risks(days_window=days)

    @staticmethod
    def get_supplier_comparison(product_query: str) -> Dict[str, Any]:
        """Finds product and compares available suppliers with prices and lead times."""
        products = AgentTools.query_stock(product_query)
        if not products:
            return {"error": f"No product found matching '{product_query}'"}
        
        target = products[0]
        engine = ReorderEngine(target["id"])
        eval_result = engine.evaluate()
        return {
            "product": target["name"],
            "tamil_name": target.get("tamil_name"),
            "current_stock": target["current_stock"],
            "unit": target["unit"],
            "best_supplier": eval_result.get("best_supplier"),
            "all_supplier_options": eval_result.get("supplier_options", [])
        }

    @staticmethod
    def get_top_selling_products(limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top products by sales volume in the past 30 days."""
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.id, p.name, p.tamil_name, p.unit,
                       COALESCE(SUM(si.quantity), 0) as units_sold,
                       ROUND(COALESCE(SUM(si.total), 0), 2) as revenue
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.created_at) >= DATE('now', '-30 days')
                GROUP BY p.id
                ORDER BY units_sold DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_high_profit_low_stock() -> List[Dict[str, Any]]:
        """Finds high-margin products that are running low on stock."""
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.id, p.name, p.tamil_name, p.selling_price, p.purchase_price,
                       ROUND((p.selling_price - p.purchase_price), 2) as unit_profit,
                       ROUND(((p.selling_price - p.purchase_price) / p.selling_price * 100), 1) as margin_pct,
                       i.current_stock, p.reorder_level
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                WHERE p.is_active = 1 
                  AND i.current_stock <= p.reorder_level
                  AND ((p.selling_price - p.purchase_price) / p.selling_price) >= 0.15
                ORDER BY margin_pct DESC, i.current_stock ASC
                LIMIT 10
                """
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def explain_product_reorder(product_query: str) -> Dict[str, Any]:
        """Provides full mathematical explanation for a product's stockout risk and reorder qty."""
        products = AgentTools.query_stock(product_query)
        if not products:
            return {"error": f"Product '{product_query}' not found."}
        target = products[0]
        engine = ReorderEngine(target["id"])
        return engine.evaluate()
