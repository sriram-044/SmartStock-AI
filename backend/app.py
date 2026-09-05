from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database.db import init_db
from backend.routes import (
    auth_routes,
    product_routes,
    inventory_routes,
    pos_routes,
    purchase_routes,
    supplier_routes,
    analytics_routes,
    ai_routes,
    report_routes
)

app = FastAPI(
    title="Inventory Management AI",
    description="An Agentic AI-Based Intelligent Inventory Monitoring, Demand Forecasting and Replenishment System for Indian Retail (Tamil Nadu)",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(inventory_routes.router)
app.include_router(pos_routes.router)
app.include_router(purchase_routes.router)
app.include_router(supplier_routes.router)
app.include_router(analytics_routes.router)
app.include_router(ai_routes.router)
app.include_router(report_routes.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Mount frontend static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.on_event("startup")
def on_startup():
    """Initializes schema and runs seeding if database is empty."""
    init_db()
    from data.seed_data import check_and_seed
    check_and_seed()
