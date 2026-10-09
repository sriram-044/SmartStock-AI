from typing import Dict, Any, List, Optional
from backend.ai.tool_registry import ToolRegistry, ToolContext


class BusinessAnalystAgent:
    """
    Specialized Business Analyst Agent.
    Evaluates revenue, product profitability margins, dead stock capital impact,
    and provides evidence-backed strategic recommendations for store management.
    """

    name = "BusinessAnalystAgent"

    def analyze_business_health(
        self,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Conducts a 360-degree financial and inventory health audit.
        """
        ctx = context or ToolContext(task_id=task_id)

        # 1. Sales & Revenue Analytics
        sales_res = ToolRegistry.execute("get_sales_analytics", {"days": 30, "top_limit": 10}, context=ctx)
        sales_data = sales_res.data if sales_res.success else {}

        # 2. Dead Stock & Capital Blockage
        dead_res = ToolRegistry.execute("identify_dead_stock", {"days_threshold": 45}, context=ctx)
        dead_data = dead_res.data if dead_res.success else {}

        # 3. High margin opportunities
        cur_inventory_res = ToolRegistry.execute("get_inventory", {"low_stock_only": True, "limit": 10}, context=ctx)
        low_stock_skus = cur_inventory_res.data if cur_inventory_res.success else []

        insights = []
        blocked_cap = dead_data.get("total_blocked_capital_inr", 0.0)
        if blocked_cap > 5000:
            insights.append(
                f"Significant capital blockage: ₹{blocked_cap:,.2f} tied up in {dead_data.get('total_dead_stock_items', 0)} stagnant items. "
                f"Recommend immediate clearance discounts (20-30%) or vendor returns."
            )

        if low_stock_skus:
            insights.append(
                f"{len(low_stock_skus)} active items are near or below reorder level. "
                f"Prioritize reordering high-velocity staples to protect daily footfall."
            )

        summary = (
            f"Business Health Summary: 30-day top revenue: ₹{sales_data.get('top_products_revenue_inr', 0.0):,.2f} "
            f"with {sales_data.get('overall_margin_percent', 0.0)}% gross margin. "
            f"Blocked capital in dead inventory: ₹{blocked_cap:,.2f}."
        )

        return {
            "agent": self.name,
            "sales_performance": sales_data,
            "dead_stock_analysis": dead_data,
            "low_stock_alerts_count": len(low_stock_skus),
            "key_strategic_insights": insights,
            "summary": summary
        }
