from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from backend.services import supplier_service
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

class SupplierCreateUpdate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    state: str = "Tamil Nadu"
    district: str = "Chennai"
    city: Optional[str] = None
    address: Optional[str] = None
    rating: float = 4.0
    reliability_score: float = 95.0
    avg_lead_time_days: int = 3
    return_rate: float = 1.0

class LinkProductRequest(BaseModel):
    product_id: int
    supplier_price: float
    moq: int = 1
    delivery_time_days: int = 3

@router.get("")
def list_suppliers(
    search: Optional[str] = Query(None),
    district: Optional[str] = Query(None)
):
    """Lists suppliers with performance ratings."""
    return supplier_service.list_suppliers(search=search, district=district)

@router.get("/{supplier_id}")
def get_supplier(supplier_id: int):
    """Retrieves single supplier and product catalog."""
    sup = supplier_service.get_supplier_by_id(supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return sup

@router.post("")
def create_supplier(
    data: SupplierCreateUpdate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Creates a supplier."""
    return supplier_service.create_supplier(data.dict())

@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    data: SupplierCreateUpdate,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Updates supplier."""
    sup = supplier_service.update_supplier(supplier_id, data.dict())
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return sup

@router.post("/{supplier_id}/products")
def link_product(
    supplier_id: int,
    req: LinkProductRequest,
    current_user: dict = Depends(require_roles([ROLE_ADMIN, ROLE_MANAGER]))
):
    """Links product to supplier catalog with pricing and MOQ."""
    supplier_service.link_product_to_supplier(
        supplier_id=supplier_id,
        product_id=req.product_id,
        price=req.supplier_price,
        moq=req.moq,
        lead_time_days=req.delivery_time_days
    )
    return {"message": "Product linked to supplier successfully"}
