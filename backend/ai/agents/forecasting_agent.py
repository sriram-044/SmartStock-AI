from typing import Dict, Any, List, Optional
from backend.ai.tool_registry import ToolRegistry, ToolContext


class ForecastingAgent:
    """
    Specialized Demand Forecasting Agent.
    Evaluates historical sales trends, tests multiple ML models,
    and produces grounded predictions with explicit confidence and uncertainty metrics.
    """

    name = "ForecastingAgent"

    def forecast_products(
        self,
        product_ids: List[int],
        days_horizon: int = 7,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Runs multi-model forecasting for requested product IDs.
        """
        ctx = context or ToolContext(task_id=task_id)
        forecasts = []
        low_data_warnings = []

        for pid in product_ids:
            # 1. Inspect sales history
            hist_res = ToolRegistry.execute("get_sales_history", {"product_id": pid, "days": 60}, context=ctx)
            hist_data = hist_res.data if hist_res.success else {}
            sales_days = hist_data.get("days_with_sales", 0)

            # 2. Run forecast model
            fc_res = ToolRegistry.execute("forecast_demand", {"product_id": pid}, context=ctx)
            if not fc_res.success:
                low_data_warnings.append(f"Product {pid}: unable to forecast ({fc_res.error})")
                continue

            fc_data = fc_res.data
            # Adjust projection to days_horizon
            daily_avg = fc_data.get("avg_daily_sales", 1.0)
            projected_demand = round(daily_avg * days_horizon, 1)

            forecasts.append({
                "product_id": pid,
                "product_name": fc_data.get("product_name"),
                "selected_model": fc_data.get("selected_model"),
                "avg_daily_sales": daily_avg,
                "projected_demand_horizon": projected_demand,
                "confidence_score": fc_data.get("confidence_score", 80.0),
                "validation_mae": fc_data.get("validation_mae", 0.0),
                "has_sufficient_history": sales_days >= 7,
                "model_comparison": fc_data.get("model_comparison", [])
            })

        summary = (
            f"Generated multi-model demand forecasts for {len(forecasts)} SKUs over {days_horizon} days. "
            f"Average forecast confidence: {round(sum(f['confidence_score'] for f in forecasts) / max(len(forecasts), 1), 1)}%."
        )

        return {
            "agent": self.name,
            "horizon_days": days_horizon,
            "forecasts": forecasts,
            "low_data_warnings": low_data_warnings,
            "summary": summary
        }
