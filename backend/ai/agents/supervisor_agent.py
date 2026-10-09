import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.ai.task_state import TaskManager, TaskStatus, StepStatus, ApprovalStatus
from backend.ai.tool_registry import ToolContext
from backend.ai.agents.inventory_agent import InventoryAgent
from backend.ai.agents.forecasting_agent import ForecastingAgent
from backend.ai.agents.supplier_agent import SupplierAgent
from backend.ai.agents.expiry_agent import ExpiryAgent
from backend.ai.agents.procurement_agent import ProcurementAgent
from backend.ai.agents.business_analyst_agent import BusinessAnalystAgent
from backend.ai.agents.feedback_agent import FeedbackAgent


class SupervisorAgent:
    """
    Central Orchestrator & Coordinator for the Multi-Agent System.
    Interprets natural language business objectives, extracts business constraints,
    constructs an execution plan, coordinates specialized subordinate agents,
    enforces budget ceilings and approval gates, and verifies task completion.
    """

    def __init__(self):
        self.inventory_agent = InventoryAgent()
        self.forecasting_agent = ForecastingAgent()
        self.supplier_agent = SupplierAgent()
        self.expiry_agent = ExpiryAgent()
        self.procurement_agent = ProcurementAgent()
        self.business_analyst_agent = BusinessAnalystAgent()
        self.feedback_agent = FeedbackAgent()

    def interpret_goal(self, objective: str, user_constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts structured constraints (budget, days, category, urgency) from natural language.
        Attempts LLM-based structured extraction first if a cloud LLM provider is active;
        always falls back seamlessly to deterministic regex & keyword heuristics.
        """
        constraints = dict(user_constraints or {})

        # Optional LLM-assisted goal parsing
        try:
            from backend.ai.llm_engine import LLMEngine
            llm_extracted = LLMEngine.interpret_structured_goal(objective)
            if llm_extracted and isinstance(llm_extracted, dict):
                for k, v in llm_extracted.items():
                    if k not in constraints and v is not None:
                        constraints[k] = v
        except Exception:
            pass

        text = objective.lower()

        # 1. Extract budget in INR (e.g. "₹15,000", "15000", "10,000", "rs 10000", "under 15000")
        if "budget_limit_inr" not in constraints:
            budget_match = re.search(r'(?:₹|rs\.?|inr|under|within|budget of)\s*([\d,]+)', text)
            if budget_match:
                try:
                    num_str = budget_match.group(1).replace(',', '')
                    constraints["budget_limit_inr"] = float(num_str)
                except ValueError:
                    pass

        # 2. Extract days horizon (e.g. "next seven days", "3 days", "next 7 days")
        if "days_horizon" not in constraints:
            days_match = re.search(r'(\d+)\s*(?:days?|naal)', text)
            if days_match:
                constraints["days_horizon"] = int(days_match.group(1))
            elif "seven days" in text or "7 days" in text or "week" in text:
                constraints["days_horizon"] = 7
            elif "three days" in text or "3 days" in text:
                constraints["days_horizon"] = 3
            else:
                constraints["days_horizon"] = 7

        # 3. Expiry awareness flag
        if "avoid_expiring" not in constraints:
            constraints["avoid_expiring"] = bool(
                "expir" in text or "shelf" in text or "waste" in text or "fefo" in text
            )

        # 4. Supplier delivery preference
        if "urgent_delivery" not in constraints:
            constraints["urgent_delivery"] = bool(
                "urgent" in text or "immediate" in text or "quick" in text or "fastest" in text or "run out before" in text
            )

        return constraints

    def execute_goal(
        self,
        objective: str,
        user_id: Optional[int] = None,
        user_role: str = "manager",
        custom_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main multi-step agentic execution loop.
        """
        # 1. Interpret goal & build task record
        constraints = self.interpret_goal(objective, custom_constraints)
        task_id = TaskManager.create_task(
            objective=objective,
            user_id=user_id,
            constraints=constraints
        )
        ctx = ToolContext(
            user_id=user_id,
            user_role=user_role,
            task_id=task_id
        )

        TaskManager.update_task_status(task_id, TaskStatus.PLANNING)

        # 2. Build structured execution plan
        plan = [
            {"step": 1, "agent": "InventoryAgent", "action": "Analyze live inventory and identify stockout risks"},
            {"step": 2, "agent": "ExpiryAgent", "action": "Audit batch shelf-life and detect expiring products"},
            {"step": 3, "agent": "ForecastingAgent", "action": "Forecast demand for products needing replenishment"},
            {"step": 4, "agent": "SupplierAgent", "action": "Compare wholesale suppliers for price and delivery time"},
            {"step": 5, "agent": "ProcurementAgent", "action": "Consolidate purchase orders and enforce budget limits"},
            {"step": 6, "agent": "ProcurementAgent", "action": "Generate approval request for proposed purchase orders"}
        ]
        TaskManager.set_task_plan(task_id, plan)

        # Step 1: Inventory Analysis
        step1_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=1,
            agent_name="InventoryAgent",
            action_type="EXECUTE_TOOL",
            description="Scanning active catalog for stockout risks",
            step_status=StepStatus.RUNNING
        )
        t0 = time.time()
        inv_result = self.inventory_agent.analyze_stock(
            days_horizon=constraints["days_horizon"],
            task_id=task_id,
            context=ctx
        )
        t1 = int((time.time() - t0) * 1000)
        TaskManager.update_task_step(
            step1_id,
            step_status=StepStatus.COMPLETED,
            tool_output=inv_result,
            reflection=inv_result.get("summary"),
            duration_ms=t1
        )

        items_to_reorder = inv_result.get("critical_stockouts", []) + inv_result.get("reorder_needed", [])

        # Step 2: Expiry Audit
        step2_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=2,
            agent_name="ExpiryAgent",
            action_type="EXECUTE_TOOL",
            description="Auditing batch shelf-life and potential waste",
            step_status=StepStatus.RUNNING
        )
        t0 = time.time()
        expiry_result = self.expiry_agent.evaluate_expiry_risks(
            days_window=30 if constraints.get("avoid_expiring") else 45,
            task_id=task_id,
            context=ctx
        )
        t2 = int((time.time() - t0) * 1000)
        TaskManager.update_task_step(
            step2_id,
            step_status=StepStatus.COMPLETED,
            tool_output=expiry_result,
            reflection=expiry_result.get("summary"),
            duration_ms=t2
        )

        # Step 3: Demand Forecasting for reorder items
        product_ids = [it["product_id"] for it in items_to_reorder[:15]]
        step3_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=3,
            agent_name="ForecastingAgent",
            action_type="EXECUTE_TOOL",
            description=f"Running ML forecasts for {len(product_ids)} items",
            step_status=StepStatus.RUNNING
        )
        t0 = time.time()
        forecast_result = self.forecasting_agent.forecast_products(
            product_ids=product_ids,
            days_horizon=constraints["days_horizon"],
            task_id=task_id,
            context=ctx
        )
        t3 = int((time.time() - t0) * 1000)
        TaskManager.update_task_step(
            step3_id,
            step_status=StepStatus.COMPLETED,
            tool_output=forecast_result,
            reflection=forecast_result.get("summary"),
            duration_ms=t3
        )

        # Step 4: Supplier Comparison
        step4_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=4,
            agent_name="SupplierAgent",
            action_type="EXECUTE_TOOL",
            description="Comparing vendor pricing, lead time, and reliability",
            step_status=StepStatus.RUNNING
        )
        t0 = time.time()
        supplier_result = self.supplier_agent.evaluate_suppliers_for_products(
            products_to_reorder=items_to_reorder,
            task_id=task_id,
            context=ctx
        )
        t4 = int((time.time() - t0) * 1000)
        TaskManager.update_task_step(
            step4_id,
            step_status=StepStatus.COMPLETED,
            tool_output=supplier_result,
            reflection=supplier_result.get("summary"),
            duration_ms=t4
        )

        # Step 5: Procurement Planning & Budget Enforcement
        step5_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=5,
            agent_name="ProcurementAgent",
            action_type="EXECUTE_TOOL",
            description="Building draft purchase orders and enforcing financial constraints",
            step_status=StepStatus.RUNNING
        )
        t0 = time.time()
        procurement_result = self.procurement_agent.prepare_procurement_plan(
            supplier_recommendations=supplier_result.get("product_recommendations", []),
            budget_limit_inr=constraints.get("budget_limit_inr"),
            task_id=task_id,
            context=ctx
        )
        t5 = int((time.time() - t0) * 1000)
        TaskManager.update_task_step(
            step5_id,
            step_status=StepStatus.COMPLETED,
            tool_output=procurement_result,
            reflection=procurement_result.get("summary"),
            duration_ms=t5
        )

        # Step 6: Human Approval Request Gating
        draft_orders = procurement_result.get("draft_orders", [])
        total_procurement_cost = sum(o["total_amount_inr"] for o in draft_orders)

        step6_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=6,
            agent_name="ProcurementAgent",
            action_type="APPROVAL_REQUEST",
            description="Gating purchase execution behind Human-In-The-Loop approval",
            step_status=StepStatus.COMPLETED,
            reflection=f"Created approval gateway for {len(draft_orders)} draft PO(s) totaling ₹{total_procurement_cost:,.2f}"
        )

        approval_ids = []
        if draft_orders:
            for order in draft_orders:
                appr_id = TaskManager.request_approval(
                    task_id=task_id,
                    action_name="CREATE_PURCHASE_ORDER",
                    proposed_payload=order,
                    justification=order.get("justification", "Inventory stockout replenishment"),
                    estimated_cost=order["total_amount_inr"],
                    requested_by_agent="ProcurementAgent"
                )
                approval_ids.append(appr_id)

            # Set task status to WAITING_FOR_APPROVAL
            TaskManager.update_task_status(
                task_id=task_id,
                status=TaskStatus.WAITING_FOR_APPROVAL,
                result_summary=(
                    f"Plan ready. Generated {len(draft_orders)} purchase order proposal(s) "
                    f"totaling ₹{total_procurement_cost:,.2f}. Awaiting manager approval."
                ),
                final_output={
                    "inventory_analysis": inv_result,
                    "expiry_audit": expiry_result,
                    "forecasts": forecast_result,
                    "supplier_evaluation": supplier_result,
                    "procurement_plan": procurement_result,
                    "approval_ids": approval_ids
                },
                approval_status=ApprovalStatus.PENDING
            )
        else:
            # If no items needed reordering
            TaskManager.update_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result_summary="All active products are currently in safe stock levels. No reorder needed.",
                final_output={
                    "inventory_analysis": inv_result,
                    "expiry_audit": expiry_result,
                    "procurement_plan": procurement_result
                },
                approval_status=ApprovalStatus.NOT_REQUIRED
            )

        return TaskManager.get_task(task_id, user_id=user_id)

    def process_approval_decision(
        self,
        task_id: str,
        approval_id: int,
        approved: bool,
        user_id: int,
        user_role: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes human approval or rejection of an action and executes approved POs safely.
        """
        # Role verification
        if user_role.lower() not in ["admin", "manager"]:
            raise PermissionError("Only Admins and Managers have authority to approve purchase orders.")

        task = TaskManager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        # Resolve approval record
        decision_res = TaskManager.resolve_approval(
            task_id=task_id,
            approval_id=approval_id,
            approved=approved,
            user_id=user_id,
            reason=reason
        )

        if not approved:
            TaskManager.update_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result_summary=f"Purchase order proposal rejected by user: {reason or 'No reason provided'}",
                approval_status=ApprovalStatus.REJECTED
            )
            return {
                "task_id": task_id,
                "status": "REJECTED",
                "message": "Purchase order was rejected. No orders submitted."
            }

        # If approved, find the payload and execute order
        matching_approval = next((a for a in task["approvals"] if a["id"] == approval_id), None)
        if not matching_approval:
            raise ValueError(f"Approval payload not found for ID {approval_id}.")

        draft_order = matching_approval["proposed_payload"]
        exec_res = self.procurement_agent.execute_approved_order(
            draft_order=draft_order,
            user_id=user_id,
            task_id=task_id,
            context=ToolContext(user_id=user_id, user_role=user_role, task_id=task_id)
        )

        if exec_res.get("success"):
            TaskManager.update_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result_summary=f"Approved and successfully created Purchase Order {exec_res['po_number']}.",
                approval_status=ApprovalStatus.APPROVED
            )
            TaskManager.add_task_step(
                task_id=task_id,
                step_number=7,
                agent_name="ProcurementAgent",
                action_type="VERIFY",
                description=f"Verified creation of PO {exec_res['po_number']}",
                step_status=StepStatus.COMPLETED,
                reflection=f"Purchase Order {exec_res['po_number']} verified and recorded in database ledger."
            )
        else:
            TaskManager.update_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_details=exec_res.get("error", "Failed to create PO in database."),
                approval_status=ApprovalStatus.APPROVED
            )

        return {
            "task_id": task_id,
            "approval_id": approval_id,
            "status": "COMPLETED" if exec_res.get("success") else "FAILED",
            "execution_result": exec_res
        }
