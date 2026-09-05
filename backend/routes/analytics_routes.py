from fastapi import APIRouter, Query
from backend.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics & KPIs"])

@router.get("/dashboard")
def get_dashboard():
    """Retrieves executive KPIs and inventory risk counts."""
    return analytics_service.get_dashboard_kpis()

@router.get("/sales-trend")
def get_sales_trend(days: int = Query(30, ge=7, le=180)):
    """Retrieves daily aggregated sales and profit trend."""
    return analytics_service.get_sales_trend(days=days)

@router.get("/category-sales")
def get_category_sales(days: int = Query(30, ge=7, le=180)):
    """Retrieves category breakdown of sales and revenue."""
    return analytics_service.get_category_sales(days=days)

@router.get("/velocity")
def get_velocity(limit: int = Query(20, ge=5, le=100)):
    """Retrieves Average Daily Sales (ADS) and profit margins ranking."""
    return analytics_service.get_product_velocity_ranking(limit=limit)
