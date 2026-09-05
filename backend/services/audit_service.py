from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.database.db import get_db, transaction
from backend.services.inventory_service import record_transaction

def start_stock_audit(notes: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Starts a physical stock audit session."""
    audit_number = f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO stock_audits (audit_number, conducted_by, status, notes, created_at)
            VALUES (?, ?, 'IN_PROGRESS', ?, CURRENT_TIMESTAMP)
            """,
            (audit_number, user_id, notes or "Routine Physical Stock Audit")
        )
        audit_id = cur.lastrowid
        return {"audit_id": audit_id, "audit_number": audit_number, "status": "IN_PROGRESS"}

def record_physical_count(audit_id: int, product_id: int, physical_stock: float) -> Dict[str, Any]:
    """
    Records counted stock for a product, calculates variance against system stock,
    and runs the discrepancy reasoner.
    """
    with transaction() as conn:
        cur = conn.execute("SELECT current_stock FROM inventory WHERE product_id = ?", (product_id,))
        inv = cur.fetchone()
        system_stock = float(inv["current_stock"]) if inv else 0.0
        variance = round(physical_stock - system_stock, 3)

        likely_cause = _analyze_discrepancy_cause(conn, product_id, variance, system_stock)

        # Upsert into stock_audit_items
        conn.execute(
            """
            INSERT INTO stock_audit_items (audit_id, product_id, system_stock, physical_stock, variance_qty, ai_likely_cause)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (audit_id, product_id, system_stock, physical_stock, variance, likely_cause)
        )
        return {
            "audit_id": audit_id,
            "product_id": product_id,
            "system_stock": system_stock,
            "physical_stock": physical_stock,
            "variance_qty": variance,
            "ai_likely_cause": likely_cause
        }

def list_audits() -> List[Dict[str, Any]]:
    """Lists past and ongoing stock audits."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT sa.*, u.full_name as conducted_by_name,
                   COUNT(sai.id) as total_items_checked,
                   COUNT(CASE WHEN ABS(sai.variance_qty) > 0.001 THEN 1 END) as discrepancy_count
            FROM stock_audits sa
            LEFT JOIN users u ON sa.conducted_by = u.id
            LEFT JOIN stock_audit_items sai ON sa.id = sai.audit_id
            GROUP BY sa.id
            ORDER BY sa.id DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_audit_details(audit_id: int) -> Optional[Dict[str, Any]]:
    """Gets audit header and all verified items with discrepancy diagnostics."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT sa.*, u.full_name as conducted_by_name
            FROM stock_audits sa
            LEFT JOIN users u ON sa.conducted_by = u.id
            WHERE sa.id = ?
            """,
            (audit_id,)
        )
        audit_row = cur.fetchone()
        if not audit_row:
            return None
        audit = dict(audit_row)

        items_cur = conn.execute(
            """
            SELECT sai.*, p.name as product_name, p.tamil_name, p.unit, p.selling_price
            FROM stock_audit_items sai
            JOIN products p ON sai.product_id = p.id
            WHERE sai.audit_id = ?
            ORDER BY ABS(sai.variance_qty) DESC
            """,
            (audit_id,)
        )
        audit["items"] = [dict(r) for r in items_cur.fetchall()]
        return audit
    finally:
        conn.close()

def reconcile_audit(audit_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Applies AUDIT_ADJUSTMENT ledger records for all discrepancies in the audit
    and marks the audit as COMPLETED.
    """
    with transaction() as conn:
        audit_cur = conn.execute("SELECT * FROM stock_audits WHERE id = ?", (audit_id,))
        audit = audit_cur.fetchone()
        if not audit:
            raise ValueError(f"Audit ID {audit_id} not found.")

        items_cur = conn.execute("SELECT * FROM stock_audit_items WHERE audit_id = ?", (audit_id,))
        items = items_cur.fetchall()

        reconciled_count = 0
        for it in items:
            variance = float(it["variance_qty"])
            if abs(variance) > 0.001:
                record_transaction(
                    conn=conn,
                    product_id=it["product_id"],
                    change_qty=variance,
                    transaction_type="AUDIT_ADJUSTMENT",
                    reference_id=audit["audit_number"],
                    user_id=user_id,
                    reason=f"Audit Reconciliation: {it['ai_likely_cause'] or 'Stock Variance Correction'}"
                )
                conn.execute(
                    "UPDATE stock_audit_items SET action_taken = 'RECONCILED' WHERE id = ?",
                    (it["id"],)
                )
                reconciled_count += 1

        conn.execute("UPDATE stock_audits SET status = 'COMPLETED' WHERE id = ?", (audit_id,))

        return {
            "audit_id": audit_id,
            "status": "COMPLETED",
            "items_reconciled": reconciled_count
        }

def _analyze_discrepancy_cause(conn, product_id: int, variance: float, system_stock: float) -> str:
    """Neutral AI diagnostic for inventory variance causes."""
    if abs(variance) < 0.001:
        return "Stock perfectly matched."

    # Look at recent transactions
    cur = conn.execute(
        """
        SELECT transaction_type, change_qty, created_at 
        FROM inventory_transactions 
        WHERE product_id = ? 
        ORDER BY id DESC LIMIT 5
        """,
        (product_id,)
    )
    recent_tx = cur.fetchall()

    if variance < 0:
        # Physical is lower than system
        abs_var = abs(variance)
        return (
            f"Physical count is lower by {abs_var} units. Possible causes: "
            "Unrecorded transit/handling damage, customer return recorded without physical placement, "
            "loose-pack checkout variance, or untracked shrinkage requiring floor review."
        )
    else:
        # Physical is higher than system
        return (
            f"Physical count is higher by {variance} units. Possible causes: "
            "Supplier over-delivery not reflected on invoice, unrecorded customer exchange return, "
            "or previous sale cancellation where stock was restocked without ledger entry."
        )
