from datetime import datetime, date
from typing import List, Dict, Any
from backend.database.db import get_db

def evaluate_expiry_risks(days_window: int = 45) -> List[Dict[str, Any]]:
    """
    Evaluates all product batches for expiry risk using First-Expired-First-Out (FEFO),
    projecting sales velocity against remaining shelf life to forecast unsold loss.
    """
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT pb.id as batch_id, pb.batch_number, pb.mfg_date, pb.expiry_date,
                   pb.remaining_qty, p.id as product_id, p.name as product_name,
                   p.tamil_name, p.unit, p.purchase_price, p.selling_price
            FROM product_batches pb
            JOIN products p ON pb.product_id = p.id
            WHERE pb.remaining_qty > 0 AND p.is_active = 1
            ORDER BY pb.expiry_date ASC
            """
        )
        batches = [dict(r) for r in cur.fetchall()]

        today = datetime.now().date()
        expiry_reports = []

        for b in batches:
            exp_date_str = b["expiry_date"]
            try:
                exp_date = datetime.strptime(exp_date_str[:10], "%Y-%m-%d").date()
            except Exception:
                continue

            days_to_expiry = (exp_date - today).days

            if days_to_expiry > days_window:
                continue # Outside risk horizon

            # Get 30-day average daily sales
            sales_cur = conn.execute(
                """
                SELECT COALESCE(SUM(si.quantity), 0.0) as sales_30d
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? AND DATE(s.created_at) >= DATE('now', '-30 days')
                """,
                (b["product_id"],)
            )
            s_row = sales_cur.fetchone()
            sales_30d = float(s_row["sales_30d"]) if s_row else 0.0
            avg_daily_sales = max(0.1, sales_30d / 30.0)

            remaining_units = float(b["remaining_qty"])
            expected_sales_before_expiry = round(max(0, days_to_expiry) * avg_daily_sales, 1)
            unsold_at_risk = round(max(0.0, remaining_units - expected_sales_before_expiry), 1)
            potential_loss_inr = round(unsold_at_risk * float(b["purchase_price"]), 2)

            if days_to_expiry <= 7:
                risk_status = "CRITICAL_EXPIRY"
                status_label = "Critical Expiry (Urgent Action)"
                status_tamil = "உடனடி காலாவதி அபாயம்"
                action = "Clearance markdown (40% discount) or immediate supplier return"
            elif days_to_expiry <= 20:
                risk_status = "EXPIRING_SOON"
                status_label = "Expiring Soon"
                status_tamil = "விரைவில் காலாவதியாகும்"
                action = "Promotional markdown (20% discount) and feature at front counter"
            else:
                risk_status = "MONITOR"
                status_label = "Shelf-life Warning"
                status_tamil = "கண்காணிப்பு தேவை"
                action = "Prioritize batch in display under FEFO rotation"

            expiry_reports.append({
                "batch_id": b["batch_id"],
                "batch_number": b["batch_number"],
                "product_id": b["product_id"],
                "product_name": b["product_name"],
                "tamil_name": b["tamil_name"],
                "unit": b["unit"],
                "expiry_date": exp_date_str,
                "days_to_expiry": days_to_expiry,
                "remaining_qty": remaining_units,
                "avg_daily_sales": round(avg_daily_sales, 2),
                "expected_sales_before_expiry": expected_sales_before_expiry,
                "unsold_units_at_risk": unsold_at_risk,
                "potential_loss_inr": potential_loss_inr,
                "risk_status": risk_status,
                "status_label": status_label,
                "status_tamil": status_tamil,
                "recommended_action": action,
                "rationale": (
                    f"Batch {b['batch_number']} expires in {days_to_expiry} days. At current velocity of "
                    f"{avg_daily_sales:.1f} {b['unit']}/day, ~{unsold_at_risk} units will remain unsold, "
                    f"costing ₹{potential_loss_inr:,.2f}. {action}."
                )
            })

        expiry_reports.sort(key=lambda x: (x["days_to_expiry"], -x["potential_loss_inr"]))
        return expiry_reports
    finally:
        conn.close()
