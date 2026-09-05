from typing import Optional, List, Dict, Any
import sqlite3
from backend.database.db import get_db, transaction
from backend.services.inventory_service import record_transaction

def list_categories() -> List[Dict[str, Any]]:
    """Returns all product categories."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT id, name, tamil_name, description FROM categories ORDER BY name")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Fetches full product details with current inventory and category name."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT p.*, c.name as category_name, c.tamil_name as category_tamil,
                   i.current_stock, i.reserved_stock,
                   s.name as supplier_name, s.avg_lead_time_days as supplier_lead_time
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
            WHERE p.id = ?
            """,
            (product_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        _enrich_product_computed_fields(res)
        return res
    finally:
        conn.close()

def get_product_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    """Fast barcode lookup for POS and scanner."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT p.*, c.name as category_name, c.tamil_name as category_tamil,
                   i.current_stock, i.reserved_stock,
                   s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
            WHERE p.barcode = ? AND p.is_active = 1
            """,
            (barcode.strip(),)
        )
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        _enrich_product_computed_fields(res)
        return res
    finally:
        conn.close()

def list_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    stock_status: Optional[str] = None, # 'CRITICAL', 'LOW', 'SAFE', 'OVERSTOCK'
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """Lists products with full pagination, search, category filter, and computed stock status."""
    conn = get_db()
    try:
        base_query = """
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
            WHERE p.is_active = 1
        """
        params = []
        if search:
            search_pat = f"%{search.strip()}%"
            base_query += " AND (p.name LIKE ? OR p.tamil_name LIKE ? OR p.barcode LIKE ? OR p.brand LIKE ?)"
            params.extend([search_pat, search_pat, search_pat, search_pat])
        if category_id:
            base_query += " AND p.category_id = ?"
            params.append(category_id)

        # Count total matching
        count_cur = conn.execute(f"SELECT COUNT(*) as cnt {base_query}", params)
        total = count_cur.fetchone()["cnt"]

        query = f"""
            SELECT p.*, c.name as category_name, c.tamil_name as category_tamil,
                   COALESCE(i.current_stock, 0.0) as current_stock,
                   COALESCE(i.reserved_stock, 0.0) as reserved_stock,
                   s.name as supplier_name, s.avg_lead_time_days as supplier_lead_time
            {base_query}
            ORDER BY p.id ASC
            LIMIT ? OFFSET ?
        """
        fetch_params = params + [limit, offset]
        cur = conn.execute(query, fetch_params)
        
        items = []
        for r in cur.fetchall():
            d = dict(r)
            _enrich_product_computed_fields(d)
            if stock_status:
                if d["stock_status"] != stock_status:
                    continue
            items.append(d)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items
        }
    finally:
        conn.close()

def create_product(data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """Creates a new product, initializes inventory, and writes opening stock transaction."""
    with transaction() as conn:
        opening_stock = float(data.get("opening_stock", 0.0))
        cur = conn.execute(
            """
            INSERT INTO products (
                barcode, name, tamil_name, category_id, subcategory, brand,
                unit, pack_size, purchase_price, selling_price, mrp, gst_rate,
                min_stock, max_stock, reorder_level, safety_stock,
                preferred_supplier_id, expiry_applicable, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                data.get("barcode"),
                data["name"],
                data.get("tamil_name"),
                data.get("category_id"),
                data.get("subcategory"),
                data.get("brand"),
                data.get("unit", "Piece"),
                data.get("pack_size"),
                float(data.get("purchase_price", 0.0)),
                float(data.get("selling_price", 0.0)),
                float(data.get("mrp", data.get("selling_price", 0.0))),
                float(data.get("gst_rate", 5.0)),
                int(data.get("min_stock", 10)),
                int(data.get("max_stock", 100)),
                int(data.get("reorder_level", 20)),
                int(data.get("safety_stock", 10)),
                data.get("preferred_supplier_id"),
                1 if data.get("expiry_applicable") else 0
            )
        )
        product_id = cur.lastrowid
        
        # Initialize inventory row
        conn.execute(
            "INSERT INTO inventory (product_id, current_stock, reserved_stock) VALUES (?, 0.0, 0.0)",
            (product_id,)
        )
        
        # Record opening stock if > 0
        if opening_stock > 0:
            record_transaction(
                conn=conn,
                product_id=product_id,
                change_qty=opening_stock,
                transaction_type="OPENING",
                reference_id="OPENING-STOCK",
                user_id=user_id,
                reason="Initial product creation stock entry"
            )
            
    return get_product_by_id(product_id)

def update_product(product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates product attributes."""
    with transaction() as conn:
        conn.execute(
            """
            UPDATE products SET
                barcode = ?, name = ?, tamil_name = ?, category_id = ?, subcategory = ?,
                brand = ?, unit = ?, pack_size = ?, purchase_price = ?, selling_price = ?,
                mrp = ?, gst_rate = ?, min_stock = ?, max_stock = ?, reorder_level = ?,
                safety_stock = ?, preferred_supplier_id = ?, expiry_applicable = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data.get("barcode"),
                data["name"],
                data.get("tamil_name"),
                data.get("category_id"),
                data.get("subcategory"),
                data.get("brand"),
                data.get("unit", "Piece"),
                data.get("pack_size"),
                float(data.get("purchase_price", 0.0)),
                float(data.get("selling_price", 0.0)),
                float(data.get("mrp", data.get("selling_price", 0.0))),
                float(data.get("gst_rate", 5.0)),
                int(data.get("min_stock", 10)),
                int(data.get("max_stock", 100)),
                int(data.get("reorder_level", 20)),
                int(data.get("safety_stock", 10)),
                data.get("preferred_supplier_id"),
                1 if data.get("expiry_applicable") else 0,
                product_id
            )
        )
    return get_product_by_id(product_id)

def delete_product(product_id: int) -> bool:
    """Soft-deletes a product by setting is_active = 0."""
    with transaction() as conn:
        cur = conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        return cur.rowcount > 0

def _enrich_product_computed_fields(d: Dict[str, Any]):
    """Calculates GST breakdown, margins, and stock status."""
    selling = float(d.get("selling_price") or 0.0)
    purchase = float(d.get("purchase_price") or 0.0)
    gst_rate = float(d.get("gst_rate") or 0.0)
    current_stock = float(d.get("current_stock") or 0.0)
    reorder_level = float(d.get("reorder_level") or 0.0)
    min_stock = float(d.get("min_stock") or 0.0)
    max_stock = float(d.get("max_stock") or 100.0)

    # Base price calculation (Price excluding GST)
    base_price = round(selling / (1 + (gst_rate / 100.0)), 2)
    gst_amount = round(selling - base_price, 2)
    profit = round(selling - purchase, 2)
    margin_pct = round((profit / selling * 100.0), 2) if selling > 0 else 0.0

    # Stock Status
    if current_stock <= 0:
        status = "OUT_OF_STOCK"
        status_label = "Out of Stock"
        status_tamil = "கையிருப்பில் இல்லை"
    elif current_stock <= min_stock:
        status = "CRITICAL"
        status_label = "Critical Stock"
        status_tamil = "மிகக் குறைவான இருப்பு"
    elif current_stock <= reorder_level:
        status = "LOW"
        status_label = "Reorder Soon"
        status_tamil = "மறுஆர்டர் தேவை"
    elif current_stock > max_stock:
        status = "OVERSTOCK"
        status_label = "Overstock"
        status_tamil = "அதிக இருப்பு"
    else:
        status = "SAFE"
        status_label = "Safe"
        status_tamil = "பாதுகாப்பானது"

    d["base_price"] = base_price
    d["gst_amount"] = gst_amount
    d["profit"] = profit
    d["profit_margin_pct"] = margin_pct
    d["stock_status"] = status
    d["stock_status_label"] = status_label
    d["stock_status_tamil"] = status_tamil
    d["inventory_value"] = round(current_stock * purchase, 2)
