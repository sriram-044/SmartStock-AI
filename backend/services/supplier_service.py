from typing import Optional, List, Dict, Any
from backend.database.db import get_db, transaction

def list_suppliers(search: Optional[str] = None, district: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns suppliers with performance metrics."""
    conn = get_db()
    try:
        query = "SELECT * FROM suppliers WHERE 1=1"
        params = []
        if search:
            query += " AND (name LIKE ? OR contact_person LIKE ? OR phone LIKE ?)"
            pat = f"%{search.strip()}%"
            params.extend([pat, pat, pat])
        if district:
            query += " AND district = ?"
            params.append(district)
        query += " ORDER BY rating DESC, reliability_score DESC"
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_supplier_by_id(supplier_id: int) -> Optional[Dict[str, Any]]:
    """Fetches supplier details and their supplied product catalog."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        supplier_row = cur.fetchone()
        if not supplier_row:
            return None
        supplier = dict(supplier_row)
        
        # Get products supplied
        p_cur = conn.execute(
            """
            SELECT sp.id as map_id, sp.supplier_price, sp.moq, sp.delivery_time_days,
                   p.id as product_id, p.name as product_name, p.tamil_name, p.unit, p.selling_price
            FROM supplier_products sp
            JOIN products p ON sp.product_id = p.id
            WHERE sp.supplier_id = ?
            """,
            (supplier_id,)
        )
        supplier["products"] = [dict(r) for r in p_cur.fetchall()]
        return supplier
    finally:
        conn.close()

def create_supplier(data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new supplier."""
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO suppliers (
                name, contact_person, phone, email, state, district, city, address,
                rating, reliability_score, avg_lead_time_days, return_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data.get("contact_person"),
                data.get("phone"),
                data.get("email"),
                data.get("state", "Tamil Nadu"),
                data.get("district", "Chennai"),
                data.get("city"),
                data.get("address"),
                float(data.get("rating", 4.0)),
                float(data.get("reliability_score", 95.0)),
                int(data.get("avg_lead_time_days", 3)),
                float(data.get("return_rate", 1.0))
            )
        )
        supplier_id = cur.lastrowid
    return get_supplier_by_id(supplier_id)

def update_supplier(supplier_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates supplier profile."""
    with transaction() as conn:
        conn.execute(
            """
            UPDATE suppliers SET
                name = ?, contact_person = ?, phone = ?, email = ?, state = ?,
                district = ?, city = ?, address = ?, rating = ?, reliability_score = ?,
                avg_lead_time_days = ?, return_rate = ?
            WHERE id = ?
            """,
            (
                data["name"],
                data.get("contact_person"),
                data.get("phone"),
                data.get("email"),
                data.get("state", "Tamil Nadu"),
                data.get("district", "Chennai"),
                data.get("city"),
                data.get("address"),
                float(data.get("rating", 4.0)),
                float(data.get("reliability_score", 95.0)),
                int(data.get("avg_lead_time_days", 3)),
                float(data.get("return_rate", 1.0)),
                supplier_id
            )
        )
    return get_supplier_by_id(supplier_id)

def link_product_to_supplier(supplier_id: int, product_id: int, price: float, moq: int, lead_time_days: int):
    """Maps a product to a supplier catalog."""
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO supplier_products (supplier_id, product_id, supplier_price, moq, delivery_time_days)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(supplier_id, product_id) DO UPDATE SET
                supplier_price = excluded.supplier_price,
                moq = excluded.moq,
                delivery_time_days = excluded.delivery_time_days
            """,
            (supplier_id, product_id, price, moq, lead_time_days)
        )
