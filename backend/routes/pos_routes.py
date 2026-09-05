from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.services import pos_service
from backend.services.inventory_service import InsufficientStockError
from backend.auth.roles import get_current_user

router = APIRouter(prefix="/api/pos", tags=["POS Billing"])

class CartItem(BaseModel):
    product_id: int
    quantity: float
    discount: float = 0.0

class CartPreviewRequest(BaseModel):
    items: List[CartItem]

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    payment_method: str = "CASH"
    customer_name: Optional[str] = "Walk-in Customer"
    customer_phone: Optional[str] = None
    notes: Optional[str] = None

class ReturnRequest(BaseModel):
    sale_id: Optional[int] = None
    product_id: int
    quantity: float
    refund_amount: float
    return_reason: str
    customer_name: Optional[str] = None

@router.post("/preview")
def preview_cart(req: CartPreviewRequest):
    """Pre-calculates subtotals, GST split, and bill total for live POS display."""
    try:
        return pos_service.calculate_cart_preview([item.dict() for item in req.items])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/checkout")
def checkout(req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    """Processes POS checkout, validates stock, reduces inventory, and generates invoice."""
    try:
        invoice = pos_service.create_sale_invoice(
            data=req.dict(),
            user_id=current_user["id"]
        )
        return invoice
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Stock constraint: '{e.product_name}' only has {e.available} units available (Requested: {e.requested})."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sales")
def list_sales(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Lists past sales invoices."""
    return pos_service.list_sales(limit=limit, offset=offset, date_from=date_from, date_to=date_to)

@router.get("/sales/{sale_id}")
def get_sale(sale_id: int):
    """Retrieves full invoice with line items for viewing or thermal receipt printing."""
    sale = pos_service.get_sale_by_id(sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    return sale

@router.post("/returns")
def process_return(req: ReturnRequest, current_user: dict = Depends(get_current_user)):
    """Processes a customer return, replenishing stock and logging refund."""
    try:
        return pos_service.process_customer_return(req.dict(), user_id=current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
