from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.database.db import get_db, transaction
from backend.services.inventory_service import record_transaction, InsufficientStockError

def calculate_cart_preview(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates item subtotals, GST splits (CGST & SGST), discounts, and final bill amount
    before saving to database.
    """
    conn = get_db()
    try:
        enriched_items = []
        subtotal = 0.0
        total_gst = 0.0
        total_discount = 0.0
        
        for it in items:
            product_id = it["product_id"]
            qty = float(it["quantity"])
            cur = conn.execute(
                """
                SELECT p.*, i.current_stock 
                FROM products p 
                LEFT JOIN inventory i ON p.id = i.product_id 
                WHERE p.id = ?
                """,
                (product_id,)
            )
            p = cur.fetchone()
            if not p:
                raise ValueError(f"Product ID {product_id} not found.")
                
            selling_price = float(p["selling_price"])
            mrp = float(p["mrp"])
            gst_rate = float(p["gst_rate"])
            current_stock = float(p["current_stock"] or 0.0)
            
            # Base price before tax
            base_unit_price = selling_price / (1.0 + (gst_rate / 100.0))
            item_subtotal = round(base_unit_price * qty, 2)
            item_gst = round((selling_price - base_unit_price) * qty, 2)
            item_cgst = round(item_gst / 2.0, 2)
            item_sgst = round(item_gst - item_cgst, 2)
            
            discount = float(it.get("discount", 0.0))
            line_total = round((selling_price * qty) - discount, 2)
            
            subtotal += item_subtotal
            total_gst += item_gst
            total_discount += discount
            
            enriched_items.append({
                "product_id": product_id,
                "product_name": p["name"],
                "tamil_name": p["tamil_name"],
                "barcode": p["barcode"],
                "unit": p["unit"],
                "current_stock": current_stock,
                "quantity": qty,
                "mrp": mrp,
                "selling_price": selling_price,
                "base_unit_price": round(base_unit_price, 2),
                "gst_rate": gst_rate,
                "gst_amount": item_gst,
                "cgst_amount": item_cgst,
                "sgst_amount": item_sgst,
                "discount": discount,
                "line_total": line_total
            })
            
        grand_total = round(sum(it["line_total"] for it in enriched_items), 2)
        return {
            "items": enriched_items,
            "subtotal": round(subtotal, 2),
            "gst_amount": round(total_gst, 2),
            "cgst_amount": round(total_gst / 2.0, 2),
            "sgst_amount": round(total_gst / 2.0, 2),
            "discount_amount": round(total_discount, 2),
            "total_amount": grand_total
        }
    finally:
        conn.close()

def create_sale_invoice(data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Creates a sales bill, decrements inventory stock for each item,
    and logs immutable SALE transactions in the ledger.
    """
    items = data.get("items", [])
    if not items:
        raise ValueError("Cannot checkout an empty cart.")
        
    payment_method = data.get("payment_method", "CASH").upper()
    if payment_method not in ["CASH", "UPI", "DEBIT_CARD", "CREDIT_CARD", "CREDIT"]:
        payment_method = "CASH"
        
    calculation = calculate_cart_preview(items)
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with transaction() as conn:
        # Check sufficient stock for all items
        for it in calculation["items"]:
            cur_stock = conn.execute("SELECT current_stock FROM inventory WHERE product_id = ?", (it["product_id"],))
            stock_row = cur_stock.fetchone()
            avail = float(stock_row["current_stock"]) if stock_row else 0.0
            if avail < it["quantity"]:
                raise InsufficientStockError(it["product_name"], avail, it["quantity"])

        # Insert sales record
        cur = conn.execute(
            """
            INSERT INTO sales (
                invoice_number, user_id, customer_name, customer_phone,
                subtotal, discount_amount, gst_amount, total_amount,
                payment_method, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                invoice_number,
                user_id,
                data.get("customer_name") or "Walk-in Customer",
                data.get("customer_phone"),
                calculation["subtotal"],
                calculation["discount_amount"],
                calculation["gst_amount"],
                calculation["total_amount"],
                payment_method,
                data.get("notes")
            )
        )
        sale_id = cur.lastrowid

        # Insert sale items and deduct inventory
        for it in calculation["items"]:
            conn.execute(
                """
                INSERT INTO sale_items (
                    sale_id, product_id, quantity, unit_price, mrp,
                    gst_rate, gst_amount, discount, total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    it["product_id"],
                    it["quantity"],
                    it["selling_price"],
                    it["mrp"],
                    it["gst_rate"],
                    it["gst_amount"],
                    it["discount"],
                    it["line_total"]
                )
            )
            
            # Atomically decrement inventory with ledger audit entry
            record_transaction(
                conn=conn,
                product_id=it["product_id"],
                change_qty=-it["quantity"],
                transaction_type="SALE",
                reference_id=invoice_number,
                user_id=user_id,
                reason=f"POS Sale Invoice #{invoice_number}"
            )

    return get_sale_by_id(sale_id)

def get_sale_by_id(sale_id: int) -> Optional[Dict[str, Any]]:
    """Gets sale invoice with all lines and customer info."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT s.*, u.full_name as cashier_name
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.id = ?
            """,
            (sale_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        sale = dict(row)
        
        item_cur = conn.execute(
            """
            SELECT si.*, p.name as product_name, p.tamil_name, p.barcode, p.unit
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
            """,
            (sale_id,)
        )
        sale["items"] = [dict(r) for r in item_cur.fetchall()]
        return sale
    finally:
        conn.close()

def list_sales(limit: int = 50, offset: int = 0, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists recent sales invoices."""
    conn = get_db()
    try:
        query = """
            SELECT s.*, u.full_name as cashier_name,
                   (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) as item_count
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND s.created_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND s.created_at <= ?"
            params.append(date_to)
            
        query += " ORDER BY s.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def process_customer_return(data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Processes customer product return, replenishing inventory stock and recording CUSTOMER_RETURN in ledger.
    """
    with transaction() as conn:
        product_id = data["product_id"]
        qty = float(data["quantity"])
        refund_amount = float(data["refund_amount"])
        reason = data["return_reason"]
        return_number = f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur = conn.execute(
            """
            INSERT INTO returns (
                return_number, sale_id, product_id, quantity,
                refund_amount, return_reason, customer_name, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                return_number,
                data.get("sale_id"),
                product_id,
                qty,
                refund_amount,
                reason,
                data.get("customer_name"),
                user_id
            )
        )
        return_id = cur.lastrowid
        
        # Increase inventory
        record_transaction(
            conn=conn,
            product_id=product_id,
            change_qty=qty,
            transaction_type="CUSTOMER_RETURN",
            reference_id=return_number,
            user_id=user_id,
            reason=f"Customer Return: {reason}"
        )
        
        return {
            "return_id": return_id,
            "return_number": return_number,
            "product_id": product_id,
            "quantity": qty,
            "refund_amount": refund_amount,
            "status": "SUCCESS"
        }
