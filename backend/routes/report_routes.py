from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.database.db import get_db, transaction
from backend.services import audit_service
from backend.config import TAMIL_NADU_DISTRICTS
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api", tags=["Reports, Settings & Audits"])

class ShopSettingsUpdate(BaseModel):
    shop_name: str
    tamil_shop_name: Optional[str] = None
    gstin: Optional[str] = None
    state: str = "Tamil Nadu"
    district: str = "Chennai"
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    low_stock_threshold_percent: float = 20.0
    default_lead_time_days: int = 4

class AuditStartRequest(BaseModel):
    notes: Optional[str] = None

class AuditCountRequest(BaseModel):
    product_id: int
    physical_stock: float

# SETTINGS
@router.get("/settings")
def get_settings():
    """Gets shop configuration and regional parameters."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT * FROM settings LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

@router.put("/settings")
def update_settings(
    data: ShopSettingsUpdate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN]))
):
    """Admin-only: Updates shop profile and Tamil Nadu district location."""
    with transaction() as conn:
        conn.execute(
            """
            UPDATE settings SET
                shop_name = ?, tamil_shop_name = ?, gstin = ?, state = ?,
                district = ?, city = ?, address = ?, phone = ?,
                low_stock_threshold_percent = ?, default_lead_time_days = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                data.shop_name,
                data.tamil_shop_name,
                data.gstin,
                data.state,
                data.district,
                data.city,
                data.address,
                data.phone,
                data.low_stock_threshold_percent,
                data.default_lead_time_days
            )
        )
    return get_settings()

@router.get("/districts")
def get_districts():
    """Lists supported Tamil Nadu districts."""
    return {"state": "Tamil Nadu", "districts": TAMIL_NADU_DISTRICTS}

# PHYSICAL STOCK AUDIT
@router.get("/audits")
def list_audits():
    """Lists stock audit sessions."""
    return audit_service.list_audits()

@router.get("/audits/{audit_id}")
def get_audit(audit_id: int):
    """Gets audit details and discrepancies."""
    res = audit_service.get_audit_details(audit_id)
    if not res:
        raise HTTPException(status_code=404, detail="Audit not found")
    return res

@router.post("/audits/start")
def start_audit(req: AuditStartRequest, current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))):
    """Initiates a physical inventory audit."""
    return audit_service.start_stock_audit(notes=req.notes, user_id=current_user["id"])

@router.post("/audits/{audit_id}/count")
def record_count(
    audit_id: int,
    req: AuditCountRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Records physical count and calculates discrepancy."""
    return audit_service.record_physical_count(
        audit_id=audit_id,
        product_id=req.product_id,
        physical_stock=req.physical_stock
    )

@router.post("/audits/{audit_id}/reconcile")
def reconcile_audit(
    audit_id: int,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """One-click reconciliation of verified audit discrepancies into the ledger."""
    try:
        return audit_service.reconcile_audit(audit_id, user_id=current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
