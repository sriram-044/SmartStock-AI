from typing import Dict, Any, List, Optional
from backend.ai.tool_registry import ToolRegistry, ToolContext
from backend.ai.task_state import TaskManager


class ProcurementAgent:
    """
    Specialized Procurement & Financial Governance Agent.
    Prepares draft Purchase Orders, calculates GST breakdowns, validates budgets,
    enforces Human-In-The-Loop approvals, and executes verified purchases.
    """

    name = "ProcurementAgent"

    def prepare_procurement_plan(
        self,
        supplier_recommendations: List[Dict[str, Any]],
        budget_limit_inr: Optional[float] = None,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive purchasing plan from supplier recommendations,
        respecting the assigned budget limit.
        """
        ctx = context or ToolContext(task_id=task_id, user_role="manager")

        # 1. Group items by supplier
        supplier_orders: Dict[int, Dict[str, Any]] = {}
        for r in supplier_recommendations:
            sup_id = r["selected_supplier_id"]
            if sup_id not in supplier_orders:
                supplier_orders[sup_id] = {
                    "supplier_id": sup_id,
                    "supplier_name": r["supplier_name"],
                    "lead_time_days": r["lead_time_days"],
                    "items": []
                }
            supplier_orders[sup_id]["items"].append({
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "quantity": float(r["adjusted_order_qty"]),
                "unit_cost": float(r["unit_cost"]),
                "gst_rate": 5.0
            })

        # 2. Build draft PO for each supplier
        draft_orders = []
        total_projected_spend = 0.0

        for sup_id, order_data in supplier_orders.items():
            draft_res = ToolRegistry.execute(
                "create_purchase_order_draft",
                {
                    "supplier_id": sup_id,
                    "items": order_data["items"],
                    "business_justification": "Restock plan from Agentic AI"
                },
                context=ctx
            )
            if draft_res.success:
                draft_info = draft_res.data
                draft_orders.append(draft_info)
                total_projected_spend += draft_info["total_amount_inr"]

        # 3. Budget Validation
        budget_check = {
            "budget_limit_inr": budget_limit_inr,
            "total_spend_inr": round(total_projected_spend, 2),
            "is_within_budget": True if budget_limit_inr is None else (total_projected_spend <= budget_limit_inr),
            "remaining_budget_inr": round(budget_limit_inr - total_projected_spend, 2) if budget_limit_inr else None
        }

        # If budget exceeded, trim lowest priority orders
        trimmed_orders = draft_orders
        if budget_limit_inr is not None and total_projected_spend > budget_limit_inr:
            trimmed_orders, adjusted_spend = self._adjust_to_budget(draft_orders, budget_limit_inr)
            budget_check["is_within_budget"] = True
            budget_check["adjusted_total_spend_inr"] = round(adjusted_spend, 2)
            budget_check["remaining_budget_inr"] = round(budget_limit_inr - adjusted_spend, 2)
            budget_check["notes"] = "Quantities were adjusted to strictly satisfy the designated spending budget."

        summary = (
            f"Prepared procurement plan with {len(trimmed_orders)} purchase order(s). "
            f"Total estimated procurement cost: ₹{budget_check.get('adjusted_total_spend_inr', total_projected_spend):,.2f}. "
            f"Budget compliant: {budget_check['is_within_budget']}."
        )

        return {
            "agent": self.name,
            "draft_orders": trimmed_orders,
            "budget_analysis": budget_check,
            "requires_human_approval": True,
            "summary": summary
        }

    def _adjust_to_budget(
        self,
        draft_orders: List[Dict[str, Any]],
        budget_limit: float
    ) -> (List[Dict[str, Any]], float):
        """Scales or trims purchase orders to fit within budget."""
        current_total = sum(o["total_amount_inr"] for o in draft_orders)
        if current_total <= budget_limit or current_total == 0:
            return draft_orders, current_total

        scale_factor = (budget_limit * 0.95) / current_total
        adjusted_orders = []
        new_total = 0.0

        for o in draft_orders:
            adj_items = []
            adj_subtotal = 0.0
            adj_gst = 0.0
            for it in o["items"]:
                scaled_qty = max(1.0, float(int(it["quantity"] * scale_factor)))
                line_cost = round(scaled_qty * it["unit_cost"], 2)
                line_gst = round(line_cost * (it["gst_rate"] / 100.0), 2)
                item_total = line_cost + line_gst

                # Ensure strict budget compliance
                if (new_total + item_total) > budget_limit:
                    rem = budget_limit - new_total
                    unit_with_gst = it["unit_cost"] * (1 + it["gst_rate"] / 100.0)
                    fit_qty = int(rem / unit_with_gst)
                    if fit_qty > 0:
                        line_cost = round(fit_qty * it["unit_cost"], 2)
                        line_gst = round(line_cost * (it["gst_rate"] / 100.0), 2)
                        adj_subtotal += line_cost
                        adj_gst += line_gst
                        new_total += (line_cost + line_gst)
                        adj_items.append({
                            **it,
                            "quantity": float(fit_qty),
                            "line_cost": line_cost,
                            "line_gst": line_gst
                        })
                    break
                else:
                    adj_subtotal += line_cost
                    adj_gst += line_gst
                    new_total += item_total
                    adj_items.append({
                        **it,
                        "quantity": scaled_qty,
                        "line_cost": line_cost,
                        "line_gst": line_gst
                    })

            if adj_items:
                order_total = round(adj_subtotal + adj_gst, 2)
                adjusted_orders.append({
                    **o,
                    "items": adj_items,
                    "subtotal_inr": round(adj_subtotal, 2),
                    "gst_amount_inr": round(adj_gst, 2),
                    "total_amount_inr": order_total
                })

        return adjusted_orders, round(new_total, 2)

    def execute_approved_order(
        self,
        draft_order: Dict[str, Any],
        user_id: int,
        task_id: Optional[str] = None,
        context: Optional[ToolContext] = None
    ) -> Dict[str, Any]:
        """
        Executes an officially approved PO into the database.
        """
        ctx = context or ToolContext(user_id=user_id, user_role="manager", task_id=task_id)

        items_payload = [
            {
                "product_id": it["product_id"],
                "quantity": it["quantity"],
                "unit_cost": it["unit_cost"],
                "gst_rate": it.get("gst_rate", 5.0)
            }
            for it in draft_order["items"]
        ]

        sub_res = ToolRegistry.execute(
            "submit_approved_purchase_order",
            {
                "supplier_id": draft_order["supplier_id"],
                "items": items_payload,
                "invoice_number": f"AI-PO-{task_id or 'DIR'}"
            },
            context=ctx
        )
        if not sub_res.success:
            return {"success": False, "error": sub_res.error}

        po_info = sub_res.data
        # Verify creation
        ver_res = ToolRegistry.execute(
            "verify_purchase_order",
            {"po_number": po_info["po_number"]},
            context=ctx
        )

        return {
            "success": True,
            "po_number": po_info["po_number"],
            "supplier_id": draft_order["supplier_id"],
            "supplier_name": draft_order.get("supplier_name"),
            "total_amount": po_info["total_amount"],
            "verified": ver_res.data.get("verified", False) if ver_res.success else False
        }
