from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.database.db import get_db, transaction
from backend.services.inventory_service import record_transaction

def list_purchases(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Lists purchase orders with supplier details."""
    conn = get_db()
    try:
        query = """
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone,
                   u.full_name as creator_name
            FROM purchases po
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u ON po.created_by = u.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND po.status = ?"
            params.append(status)
        query += " ORDER BY po.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = conn.execute(query, params)
        orders = [dict(r) for r in cur.fetchall()]
        
        # Attach line items
        for o in orders:
            item_cur = conn.execute(
                """
                SELECT pi.*, p.name as product_name, p.tamil_name, p.unit
                FROM purchase_items pi
                JOIN products p ON pi.product_id = p.id
                WHERE pi.purchase_id = ?
                """,
                (o["id"],)
            )
            o["items"] = [dict(r) for r in item_cur.fetchall()]
        return orders
    finally:
        conn.close()

def get_purchase_by_id(purchase_id: int) -> Optional[Dict[str, Any]]:
    """Gets single purchase order with items."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone,
                   s.address as supplier_address, u.full_name as creator_name
            FROM purchases po
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u ON po.created_by = u.id
            WHERE po.id = ?
            """,
            (purchase_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        po = dict(row)
        item_cur = conn.execute(
            """
            SELECT pi.*, p.name as product_name, p.tamil_name, p.unit
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
            """,
            (purchase_id,)
        )
        po["items"] = [dict(r) for r in item_cur.fetchall()]
        return po
    finally:
        conn.close()

def create_purchase_order(data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """Creates a purchase order."""
    with transaction() as conn:
        supplier_id = data["supplier_id"]
        items = data.get("items", [])
        if not items:
            raise ValueError("Purchase order must have at least one product item.")
            
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subtotal = 0.0
        gst_total = 0.0
        
        # Calculate totals
        for item in items:
            qty = float(item["quantity"])
            cost = float(item["unit_cost"])
            gst_rate = float(item.get("gst_rate", 5.0))
            line_cost = round(qty * cost, 2)
            line_gst = round(line_cost * (gst_rate / 100.0), 2)
            subtotal += line_cost
            gst_total += line_gst

        total_amount = round(subtotal + gst_total, 2)

        cur = conn.execute(
            """
            INSERT INTO purchases (
                po_number, supplier_id, status, expected_delivery,
                subtotal, gst_amount, total_amount, invoice_number, created_by
            ) VALUES (?, ?, 'ORDERED', ?, ?, ?, ?, ?, ?)
            """,
            (
                po_number,
                supplier_id,
                data.get("expected_delivery"),
                subtotal,
                gst_total,
                total_amount,
                data.get("invoice_number"),
                user_id
            )
        )
        purchase_id = cur.lastrowid
        
        for item in items:
            qty = float(item["quantity"])
            cost = float(item["unit_cost"])
            gst_rate = float(item.get("gst_rate", 5.0))
            line_total = round(qty * cost * (1 + gst_rate / 100.0), 2)
            conn.execute(
                """
                INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, gst_rate, total_cost)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (purchase_id, item["product_id"], qty, cost, gst_rate, line_total)
            )
            
    return get_purchase_by_id(purchase_id)

def receive_purchase_order(purchase_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Marks a purchase order as RECEIVED, atomically increments inventory stock,
    and writes PURCHASE ledger transactions.
    """
    with transaction() as conn:
        cur = conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,))
        po = cur.fetchone()
        if not po:
            raise ValueError(f"Purchase order ID {purchase_id} not found.")
        if po["status"] == "RECEIVED":
            raise ValueError("This purchase order has already been received.")
            
        items_cur = conn.execute("SELECT * FROM purchase_items WHERE purchase_id = ?", (purchase_id,))
        items = items_cur.fetchall()
        
        for item in items:
            p_id = item["product_id"]
            qty = float(item["quantity"])
            
            # Atomically increase inventory and record ledger entry
            record_transaction(
                conn=conn,
                product_id=p_id,
                change_qty=qty,
                transaction_type="PURCHASE",
                reference_id=po["po_number"],
                user_id=user_id,
                reason=f"Goods Inward from Supplier PO #{po['po_number']}"
            )
            
        conn.execute(
            """
            UPDATE purchases 
            SET status = 'RECEIVED', actual_delivery = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (purchase_id,)
        )
        
    return get_purchase_by_id(purchase_id)
