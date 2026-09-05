from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from backend.services import inventory_service
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api/inventory", tags=["Inventory Ledger"])

class StockAdjustmentRequest(BaseModel):
    product_id: int
    physical_stock: float
    reason: str

class LossRecordRequest(BaseModel):
    product_id: int
    quantity: float
    is_expired: bool = False
    reason: str

@router.get("/ledger")
def get_ledger(
    product_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Retrieves immutable audit trail of inventory transactions."""
    return inventory_service.get_ledger_history(
        product_id=product_id,
        transaction_type=transaction_type,
        limit=limit,
        offset=offset
    )

@router.get("/{product_id}/stock")
def get_stock(product_id: int):
    """Gets real-time stock levels and reorder parameters."""
    try:
        return inventory_service.get_current_stock(product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/adjust")
def adjust_stock(
    req: StockAdjustmentRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Records an explicit AUDIT_ADJUSTMENT to align system stock with verified physical stock."""
    try:
        return inventory_service.adjust_stock(
            product_id=req.product_id,
            new_physical_stock=req.physical_stock,
            user_id=current_user["id"],
            reason=req.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/loss")
def record_loss(
    req: LossRecordRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Records damage or expired inventory reduction."""
    try:
        new_balance = inventory_service.record_loss(
            product_id=req.product_id,
            qty=req.quantity,
            is_expired=req.is_expired,
            user_id=current_user["id"],
            reason=req.reason
        )
        return {"product_id": req.product_id, "new_balance": new_balance, "status": "RECORDED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
