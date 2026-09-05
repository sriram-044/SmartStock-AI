from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlite3
from backend.database.db import get_db, transaction

class InsufficientStockError(Exception):
    def __init__(self, product_name: str, available: float, requested: float):
        super().__init__(f"Insufficient stock for '{product_name}'. Available: {available}, Requested: {requested}")
        self.product_name = product_name
        self.available = available
        self.requested = requested

def record_transaction(
    conn: sqlite3.Connection,
    product_id: int,
    change_qty: float,
    transaction_type: str,
    reference_id: Optional[str] = None,
    user_id: Optional[int] = None,
    reason: Optional[str] = None
) -> float:
    """
    Atomically updates inventory table and writes an immutable record in inventory_transactions.
    Returns the new balance after transaction.
    """
    cur = conn.execute("SELECT current_stock, reserved_stock FROM inventory WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    if not row:
        cur_prod = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        p = cur_prod.fetchone()
        prod_name = p["name"] if p else f"ID {product_id}"
        raise ValueError(f"Product '{prod_name}' has no inventory record.")

    current_stock = float(row["current_stock"])
    new_balance = current_stock + change_qty

    # Negative balance is not allowed for sales/damage
    if new_balance < -0.0001:
        cur_prod = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        p = cur_prod.fetchone()
        prod_name = p["name"] if p else f"ID {product_id}"
        raise InsufficientStockError(prod_name, current_stock, abs(change_qty))

    # Update inventory table
    conn.execute(
        """
        UPDATE inventory 
        SET current_stock = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE product_id = ?
        """,
        (round(new_balance, 3), product_id)
    )

    # Insert immutable ledger entry
    conn.execute(
        """
        INSERT INTO inventory_transactions 
        (product_id, change_qty, balance_after, transaction_type, reference_id, user_id, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (product_id, round(change_qty, 3), round(new_balance, 3), transaction_type, reference_id, user_id, reason)
    )

    return round(new_balance, 3)

def get_current_stock(product_id: int) -> Dict[str, Any]:
    """Fetches the current stock, safety stock, and reorder levels for a product."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT p.id, p.name, p.tamil_name, p.unit, p.min_stock, p.max_stock, 
                   p.reorder_level, p.safety_stock, i.current_stock, i.reserved_stock, i.updated_at
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE p.id = ?
            """,
            (product_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Product ID {product_id} not found.")
        return dict(row)
    finally:
        conn.close()

def adjust_stock(product_id: int, new_physical_stock: float, user_id: int, reason: str) -> Dict[str, Any]:
    """Records an AUDIT_ADJUSTMENT to align system stock with verified physical stock."""
    with transaction() as conn:
        cur = conn.execute("SELECT current_stock FROM inventory WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Product ID {product_id} not found.")
        current_stock = float(row["current_stock"])
        difference = new_physical_stock - current_stock
        
        balance = record_transaction(
            conn=conn,
            product_id=product_id,
            change_qty=difference,
            transaction_type="AUDIT_ADJUSTMENT",
            reference_id=f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            reason=reason or "Physical audit stock correction"
        )
        return {
            "product_id": product_id,
            "previous_stock": current_stock,
            "adjustment_qty": difference,
            "new_stock": balance
        }

def record_loss(product_id: int, qty: float, is_expired: bool, user_id: int, reason: str) -> float:
    """Records damaged or expired inventory deductions."""
    trans_type = "EXPIRED" if is_expired else "DAMAGE"
    with transaction() as conn:
        return record_transaction(
            conn=conn,
            product_id=product_id,
            change_qty=-abs(qty),
            transaction_type=trans_type,
            reference_id=f"{trans_type[:3]}-{datetime.now().strftime('%Y%m%d%H%M')}",
            user_id=user_id,
            reason=reason
        )

def get_ledger_history(
    product_id: Optional[int] = None, 
    transaction_type: Optional[str] = None,
    limit: int = 50, 
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Retrieves transaction history with joined product and user details."""
    conn = get_db()
    try:
        query = """
            SELECT it.id, it.product_id, p.name as product_name, p.tamil_name, p.unit,
                   it.change_qty, it.balance_after, it.transaction_type, it.reference_id,
                   it.reason, it.created_at, u.username, u.full_name as user_full_name
            FROM inventory_transactions it
            JOIN products p ON it.product_id = p.id
            LEFT JOIN users u ON it.user_id = u.id
            WHERE 1=1
        """
        params = []
        if product_id:
            query += " AND it.product_id = ?"
            params.append(product_id)
        if transaction_type:
            query += " AND it.transaction_type = ?"
            params.append(transaction_type)
            
        query += " ORDER BY it.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cur = conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
