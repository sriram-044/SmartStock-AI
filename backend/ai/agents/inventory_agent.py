from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.ai.tool_registry import ToolRegistry, ToolContext
from backend.ai.task_state import TaskManager, StepStatus


class InventoryAnalysisResult(BaseModel):
    scanned_products: int
    critical_stockouts: List[Dict[str, Any]] = Field(default_factory=list)
    reorder_needed: List[Dict[str, Any]] = Field(default_factory=list)
    healthy_stock_count: int = 0
    total_reorder_units: float = 0.0
    summary: str = ""


class InventoryAgent:
    """
    Specialized Inventory Management Agent.
    Evaluates physical stock levels, runout velocity, safety stock thresholds,
    and identifies stockout risks across product categories.
    """

    name = "InventoryAgent"

    def analyze_stock(
        self,
        category_id: Optional[int] = None,
        days_horizon: int = 7,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Executes deterministic inventory scan and risk evaluation.
        """
        ctx = context or ToolContext(task_id=task_id)

        # 1. Fetch live inventory
        inv_res = ToolRegistry.execute(
            "get_inventory",
            {"category_id": category_id, "limit": 100},
            context=ctx
        )
        if not inv_res.success:
            return {"error": f"Failed to retrieve inventory: {inv_res.error}"}

        products = inv_res.data or []
        critical_stockouts = []
        reorder_needed = []
        healthy_count = 0
        total_reorder_qty = 0.0

        for p in products:
            prod_id = p["id"]
            # Evaluate statistical stockout risk
            risk_res = ToolRegistry.execute(
                "calculate_stockout_risk",
                {"product_id": prod_id},
                context=ctx
            )
            if not risk_res.success:
                continue

            risk_data = risk_res.data
            risk_lvl = risk_data.get("risk_level", "SAFE")
            rec_qty = float(risk_data.get("recommended_qty", 0.0))

            item_summary = {
                "product_id": prod_id,
                "name": p["name"],
                "tamil_name": p.get("tamil_name"),
                "current_stock": p["current_stock"],
                "unit": p.get("unit", "Piece"),
                "risk_level": risk_lvl,
                "status_label": risk_data.get("status_label"),
                "recommended_qty": rec_qty,
                "days_remaining": risk_data.get("days_remaining", 999.0),
                "best_supplier": risk_data.get("best_supplier"),
                "rationale": risk_data.get("rationale")
            }

            if risk_lvl == "CRITICAL":
                critical_stockouts.append(item_summary)
                total_reorder_qty += rec_qty
            elif risk_lvl in ["REORDER_NOW", "REORDER_SOON"]:
                reorder_needed.append(item_summary)
                total_reorder_qty += rec_qty
            else:
                healthy_count += 1

        summary_text = (
            f"Scanned {len(products)} products. "
            f"Detected {len(critical_stockouts)} critical stockout emergencies and "
            f"{len(reorder_needed)} products needing replenishment within {days_horizon} days. "
            f"Total recommended reorder volume: {round(total_reorder_qty, 1)} units."
        )

        return {
            "agent": self.name,
            "scanned_products": len(products),
            "critical_stockouts": critical_stockouts,
            "reorder_needed": reorder_needed,
            "healthy_stock_count": healthy_count,
            "total_reorder_units": round(total_reorder_qty, 1),
            "summary": summary_text
        }
