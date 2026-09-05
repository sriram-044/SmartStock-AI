from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.database.db import get_db

def analyze_dead_and_slow_stock(days_threshold: int = 45) -> List[Dict[str, Any]]:
    """
    Identifies products with zero or negligible sales over the threshold period
    while holding positive inventory, calculating blocked capital and recommended actions.
    """
    conn = get_db()
    try:
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
        cur = conn.execute(
            """
            SELECT p.id, p.name, p.tamil_name, p.category_id, c.name as category_name,
                   p.unit, p.purchase_price, p.selling_price, i.current_stock,
                   COALESCE((
                       SELECT SUM(si.quantity) 
                       FROM sale_items si 
                       JOIN sales s ON si.sale_id = s.id 
                       WHERE si.product_id = p.id AND DATE(s.created_at) >= DATE(?)
                   ), 0.0) as sales_in_period,
                   (
                       SELECT MAX(s.created_at) 
                       FROM sale_items si 
                       JOIN sales s ON si.sale_id = s.id 
                       WHERE si.product_id = p.id
                   ) as last_sale_date
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND i.current_stock > 0
            """,
            (cutoff_date,)
        )
        rows = [dict(r) for r in cur.fetchall()]

        dead_stock_items = []
        for r in rows:
            stock = float(r["current_stock"])
            sales = float(r["sales_in_period"])
            purchase = float(r["purchase_price"])
            selling = float(r["selling_price"])
            blocked_capital = round(stock * purchase, 2)
            
            # Classification
            if sales <= 0.001:
                classification = "DEAD_STOCK"
                status_label = "Dead Stock (Zero Sales)"
                status_tamil = "விற்பனையற்ற முடங்கிய இருப்பு"
                action = "Clearance markdown (25% off) or bundle with high-velocity staple"
            elif sales < (stock * 0.1):
                classification = "SLOW_MOVING"
                status_label = "Slow Moving"
                status_tamil = "மெதுவாக நகரும் இருப்பு"
                action = "Promotional discount (10% off) and halt reorders"
            else:
                continue # Normal moving stock

            # Days since last sale calculation
            last_sale = r["last_sale_date"]
            if last_sale:
                try:
                    dt = datetime.strptime(last_sale[:10], '%Y-%m-%d')
                    days_idle = (datetime.now() - dt).days
                except Exception:
                    days_idle = days_threshold
            else:
                days_idle = days_threshold + 30

            dead_stock_items.append({
                "product_id": r["id"],
                "product_name": r["name"],
                "tamil_name": r["tamil_name"],
                "category_name": r["category_name"],
                "unit": r["unit"],
                "current_stock": stock,
                "sales_in_period": sales,
                "days_idle": days_idle,
                "purchase_price": purchase,
                "selling_price": selling,
                "blocked_capital": blocked_capital,
                "classification": classification,
                "status_label": status_label,
                "status_tamil": status_tamil,
                "recommended_action": action,
                "rationale": (
                    f"Blocked capital of ₹{blocked_capital:,.2f} with only {sales} units sold in {days_threshold} days. "
                    f"Recommended: {action} to recover working capital."
                )
            })

        dead_stock_items.sort(key=lambda x: x["blocked_capital"], reverse=True)
        return dead_stock_items
    finally:
        conn.close()
