from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.services import purchase_service
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api/purchases", tags=["Purchases & Inward Orders"])

class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: float
    unit_cost: float
    gst_rate: Optional[float] = 5.0

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    expected_delivery: Optional[str] = None
    invoice_number: Optional[str] = None
    items: List[PurchaseItemCreate]

@router.get("")
def list_purchases(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Lists purchase orders."""
    return purchase_service.list_purchases(status=status, limit=limit, offset=offset)

@router.get("/{purchase_id}")
def get_purchase(purchase_id: int):
    """Retrieves single purchase order with line items."""
    po = purchase_service.get_purchase_by_id(purchase_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.post("")
def create_purchase(
    req: PurchaseOrderCreate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Creates a new purchase order."""
    try:
        return purchase_service.create_purchase_order(req.dict(), user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{purchase_id}/receive")
def receive_purchase(
    purchase_id: int,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Marks PO received and automatically replenishes inventory stock."""
    try:
        return purchase_service.receive_purchase_order(purchase_id, user_id=current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
