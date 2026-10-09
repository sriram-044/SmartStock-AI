from typing import Dict, Any, List, Optional
from backend.ai.tool_registry import ToolRegistry, ToolContext


class SupplierAgent:
    """
    Specialized Supplier Intelligence Agent.
    Evaluates real Tamil Nadu wholesale vendor records, comparing price, MOQ,
    lead times, return rates, and reliability ratings to find optimal procurement sources.
    """

    name = "SupplierAgent"

    def evaluate_suppliers_for_products(
        self,
        products_to_reorder: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Evaluates vendor options for a batch of products needing reorder.
        """
        ctx = context or ToolContext(task_id=task_id)
        supplier_recommendations = []
        supplier_groups: Dict[int, List[Dict[str, Any]]] = {}

        for item in products_to_reorder:
            pid = item["product_id"]
            runout_days = item.get("days_remaining")
            urgency_days = int(runout_days) if runout_days is not None and runout_days < 5 else None

            sup_res = ToolRegistry.execute(
                "compare_suppliers",
                {"product_id": pid, "urgency_days": urgency_days},
                context=ctx
            )
            if not sup_res.success or not sup_res.data:
                continue

            cmp_data = sup_res.data
            recommended = cmp_data.get("recommended_option")
            if not recommended:
                continue

            sup_id = recommended["supplier_id"]
            unit_price = float(recommended["supplier_price"])
            moq = int(recommended.get("moq", 1))
            lead_time = int(recommended.get("delivery_time_days", 3))
            rec_qty = max(float(item.get("recommended_qty", 10.0)), float(moq))

            recom_entry = {
                "product_id": pid,
                "product_name": item.get("name"),
                "selected_supplier_id": sup_id,
                "supplier_name": recommended.get("supplier_name"),
                "unit_cost": unit_price,
                "moq": moq,
                "lead_time_days": lead_time,
                "reliability_score": recommended.get("reliability_score", 90.0),
                "adjusted_order_qty": rec_qty,
                "estimated_line_cost": round(rec_qty * unit_price, 2),
                "cheapest_option": cmp_data.get("cheapest_option"),
                "fastest_option": cmp_data.get("fastest_option"),
                "tradeoff_notes": (
                    f"Selected {recommended.get('supplier_name')} at ₹{unit_price}/unit "
                    f"with {lead_time}d lead time and {recommended.get('reliability_score', 90.0)}% reliability."
                )
            }
            supplier_recommendations.append(recom_entry)

            # Group items by supplier for bulk purchasing
            if sup_id not in supplier_groups:
                supplier_groups[sup_id] = []
            supplier_groups[sup_id].append(recom_entry)

        summary = (
            f"Evaluated suppliers for {len(products_to_reorder)} products. "
            f"Grouped into {len(supplier_groups)} consolidated supplier vendor orders."
        )

        return {
            "agent": self.name,
            "product_recommendations": supplier_recommendations,
            "consolidated_by_supplier": supplier_groups,
            "total_estimated_spend": round(sum(r["estimated_line_cost"] for r in supplier_recommendations), 2),
            "summary": summary
        }
