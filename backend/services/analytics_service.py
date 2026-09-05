from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from backend.database.db import get_db

def get_dashboard_kpis() -> Dict[str, Any]:
    """
    Computes all executive KPIs for the dashboard:
    Total products, inventory units, inventory value (₹), today's sales & profit,
    monthly sales & profit, critical & low stock counts, dead stock count, pending AI recommendations.
    """
    conn = get_db()
    try:
        # Total products and inventory valuation
        prod_cur = conn.execute(
            """
            SELECT COUNT(p.id) as total_products,
                   COALESCE(SUM(i.current_stock), 0) as total_inventory_qty,
                   COALESCE(SUM(i.current_stock * p.purchase_price), 0) as total_inventory_value
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.is_active = 1
            """
        )
        prod_stats = dict(prod_cur.fetchone())

        # Today's Sales & Profit
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_cur = conn.execute(
            """
            SELECT COALESCE(SUM(s.total_amount), 0) as today_sales,
                   COUNT(s.id) as today_orders,
                   COALESCE(SUM(si.quantity * (si.unit_price - p.purchase_price)), 0) as today_profit
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.created_at) = DATE(?)
            """,
            (today_str,)
        )
        today_stats = dict(today_cur.fetchone())

        # This Month's Sales & Profit
        month_start_str = datetime.now().strftime('%Y-%m-01')
        month_cur = conn.execute(
            """
            SELECT COALESCE(SUM(s.total_amount), 0) as month_sales,
                   COALESCE(SUM(si.quantity * (si.unit_price - p.purchase_price)), 0) as month_profit
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.created_at) >= DATE(?)
            """,
            (month_start_str,)
        )
        month_stats = dict(month_cur.fetchone())

        # Stock Risk Distribution
        risk_cur = conn.execute(
            """
            SELECT 
                COUNT(CASE WHEN i.current_stock <= p.min_stock THEN 1 END) as critical_stock_count,
                COUNT(CASE WHEN i.current_stock > p.min_stock AND i.current_stock <= p.reorder_level THEN 1 END) as low_stock_count,
                COUNT(CASE WHEN i.current_stock > p.max_stock THEN 1 END) as overstock_count,
                COUNT(CASE WHEN i.current_stock > p.reorder_level AND i.current_stock <= p.max_stock THEN 1 END) as safe_stock_count
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE p.is_active = 1
            """
        )
        risk_stats = dict(risk_cur.fetchone())

        # Pending AI Recommendations
        recom_cur = conn.execute(
            "SELECT COUNT(*) as pending_recom_count FROM ai_recommendations WHERE status = 'PENDING'"
        )
        pending_recom_count = recom_cur.fetchone()["pending_recom_count"]

        # Expiring in next 30 days
        expiry_cur = conn.execute(
            """
            SELECT COUNT(*) as expiring_batches
            FROM product_batches
            WHERE remaining_qty > 0 AND DATE(expiry_date) <= DATE(?, '+30 days')
            """,
            (today_str,)
        )
        expiring_batches = expiry_cur.fetchone()["expiring_batches"]

        # Unresolved stock discrepancies
        disc_cur = conn.execute(
            """
            SELECT COUNT(*) as pending_discrepancies
            FROM stock_audit_items sai
            JOIN stock_audits sa ON sai.audit_id = sa.id
            WHERE sa.status = 'IN_PROGRESS' AND ABS(sai.variance_qty) > 0.001
            """
        )
        pending_discrepancies = disc_cur.fetchone()["pending_discrepancies"]

        return {
            "total_products": prod_stats["total_products"],
            "total_inventory_qty": round(prod_stats["total_inventory_qty"], 2),
            "total_inventory_value": round(prod_stats["total_inventory_value"], 2),
            "today_sales": round(today_stats["today_sales"], 2),
            "today_orders": today_stats["today_orders"],
            "today_profit": round(today_stats["today_profit"], 2),
            "month_sales": round(month_stats["month_sales"], 2),
            "month_profit": round(month_stats["month_profit"], 2),
            "critical_stock_count": risk_stats["critical_stock_count"],
            "low_stock_count": risk_stats["low_stock_count"],
            "overstock_count": risk_stats["overstock_count"],
            "safe_stock_count": risk_stats["safe_stock_count"],
            "pending_recom_count": pending_recom_count,
            "expiring_batches_count": expiring_batches,
            "pending_discrepancies_count": pending_discrepancies
        }
    finally:
        conn.close()

def get_sales_trend(days: int = 30) -> List[Dict[str, Any]]:
    """Returns day-by-day sales revenue and profit for charting."""
    conn = get_db()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cur = conn.execute(
            """
            SELECT DATE(s.created_at) as sale_date,
                   ROUND(SUM(s.total_amount), 2) as revenue,
                   COUNT(DISTINCT s.id) as orders,
                   ROUND(SUM(si.quantity * (si.unit_price - p.purchase_price)), 2) as profit
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.created_at) >= DATE(?)
            GROUP BY DATE(s.created_at)
            ORDER BY sale_date ASC
            """,
            (start_date,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_category_sales(days: int = 30) -> List[Dict[str, Any]]:
    """Returns revenue, units sold, and profit grouped by category."""
    conn = get_db()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cur = conn.execute(
            """
            SELECT c.name as category_name, c.tamil_name as category_tamil,
                   ROUND(SUM(si.total), 2) as revenue,
                   ROUND(SUM(si.quantity), 2) as units_sold,
                   ROUND(SUM(si.quantity * (si.unit_price - p.purchase_price)), 2) as profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.created_at) >= DATE(?)
            GROUP BY c.id
            ORDER BY revenue DESC
            """,
            (start_date,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_product_velocity_ranking(limit: int = 20) -> List[Dict[str, Any]]:
    """Calculates Average Daily Sales (ADS), Sales Velocity, and Margin ranking."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT p.id, p.name, p.tamil_name, p.brand, p.unit, p.selling_price, p.purchase_price,
                   i.current_stock,
                   COALESCE(SUM(si.quantity), 0.0) as total_units_30d,
                   ROUND(COALESCE(SUM(si.quantity), 0.0) / 30.0, 2) as avg_daily_sales,
                   ROUND(COALESCE(SUM(si.total), 0.0), 2) as total_revenue_30d,
                   ROUND(COALESCE(SUM(si.quantity * (si.unit_price - p.purchase_price)), 0.0), 2) as total_profit_30d
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND DATE(s.created_at) >= DATE('now', '-30 days')
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY total_units_30d DESC
            LIMIT ?
            """,
            (limit,)
        )
        results = []
        for r in cur.fetchall():
            d = dict(r)
            selling = float(d["selling_price"] or 0)
            purchase = float(d["purchase_price"] or 0)
            d["margin_pct"] = round(((selling - purchase) / selling * 100), 2) if selling > 0 else 0
            results.append(d)
        return results
    finally:
        conn.close()
