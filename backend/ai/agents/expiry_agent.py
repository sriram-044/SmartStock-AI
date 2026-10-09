from typing import Dict, Any, List, Optional
from backend.ai.tool_registry import ToolRegistry, ToolContext


class ExpiryAgent:
    """
    Specialized Expiry Prevention & Waste Reduction Agent.
    Implements FEFO (First-Expired, First-Out) shelf-life auditing, calculates potential
    spoilage losses, suggests safe inventory rotation/markdowns, and protects cash flow.
    """

    name = "ExpiryAgent"

    def evaluate_expiry_risks(
        self,
        days_window: int = 45,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Audits batches reaching expiry within the specified window.
        """
        ctx = context or ToolContext(task_id=task_id)

        exp_res = ToolRegistry.execute("identify_expiring_products", {"days_window": days_window}, context=ctx)
        if not exp_res.success:
            return {"error": f"Failed to inspect batch shelf life: {exp_res.error}"}

        expiring_items = exp_res.data or []
        critical_expiries = []
        moderate_expiries = []
        total_risk_inr = 0.0

        for it in expiring_items:
            days_left = it.get("days_to_expiry", 999)
            potential_loss = float(it.get("potential_loss_inr", 0.0))
            total_risk_inr += potential_loss

            if days_left <= 15:
                critical_expiries.append(it)
            else:
                moderate_expiries.append(it)

        summary = (
            f"Audited FEFO product batches over {days_window}-day window. "
            f"Detected {len(expiring_items)} batches approaching expiry with ₹{round(total_risk_inr, 2):,.2f} "
            f"in inventory at risk ({len(critical_expiries)} urgent batches expiring within 15 days)."
        )

        return {
            "agent": self.name,
            "days_window": days_window,
            "total_expiring_batches": len(expiring_items),
            "total_at_risk_inr": round(total_risk_inr, 2),
            "critical_batches_under_15d": critical_expiries,
            "moderate_batches": moderate_expiries,
            "all_batches": expiring_items,
            "summary": summary
        }
