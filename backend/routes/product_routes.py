from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.services import product_service
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api/products", tags=["Products"])

class ProductCreateUpdate(BaseModel):
    barcode: Optional[str] = None
    name: str
    tamil_name: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    unit: str = "Piece"
    pack_size: Optional[str] = None
    purchase_price: float = 0.0
    selling_price: float = 0.0
    mrp: Optional[float] = None
    gst_rate: float = 5.0
    min_stock: int = 10
    max_stock: int = 100
    reorder_level: int = 20
    safety_stock: int = 10
    preferred_supplier_id: Optional[int] = None
    expiry_applicable: bool = False
    opening_stock: Optional[float] = 0.0

@router.get("/categories")
def get_categories():
    """Retrieves all product categories."""
    return product_service.list_categories()

@router.get("")
def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    stock_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lists products with search and category filters."""
    return product_service.list_products(
        search=search,
        category_id=category_id,
        stock_status=stock_status,
        limit=limit,
        offset=offset
    )

@router.get("/barcode/{barcode}")
def get_by_barcode(barcode: str):
    """Fast barcode lookup for POS scanning."""
    p = product_service.get_product_by_barcode(barcode)
    if not p:
        raise HTTPException(status_code=404, detail=f"No active product found for barcode '{barcode}'")
    return p

@router.get("/{product_id}")
def get_product(product_id: int):
    """Retrieves single product details."""
    p = product_service.get_product_by_id(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("")
def create_product(
    data: ProductCreateUpdate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Creates a new product in the catalog."""
    prod = product_service.create_product(data.dict(), user_id=current_user["id"])
    return prod

@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductCreateUpdate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Updates product attributes."""
    prod = product_service.update_product(product_id, data.dict())
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: dict = Depends(require_roles([ROLE_ADMIN]))
):
    """Admin-only: Deactivates product."""
    success = product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deactivated successfully"}
