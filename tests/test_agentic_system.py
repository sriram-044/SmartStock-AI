import unittest
from backend.ai.tool_registry import ToolRegistry, ToolContext, BaseTool, ToolResult
from backend.ai.task_state import TaskManager, TaskStatus, StepStatus, ApprovalStatus
from backend.ai.agents.supervisor_agent import SupervisorAgent
from backend.ai.agents.inventory_agent import InventoryAgent
from backend.ai.agents.forecasting_agent import ForecastingAgent
from backend.ai.agents.supplier_agent import SupplierAgent
from backend.ai.agents.expiry_agent import ExpiryAgent
from backend.ai.agents.procurement_agent import ProcurementAgent
from backend.auth.roles import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER
from pydantic import BaseModel


class DummyInput(BaseModel):
    message: str


class DummyConsequentialTool(BaseTool):
    name = "dummy_consequential_tool"
    description = "Test tool for authorization and idempotency"
    input_schema = DummyInput
    required_roles = [ROLE_MANAGER, ROLE_ADMIN]
    is_consequential = True

    def run(self, validated_input: DummyInput, context: ToolContext) -> str:
        return f"Executed: {validated_input.message}"


class TestAgenticSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ToolRegistry.register(DummyConsequentialTool())

    def test_tool_registry_validation_and_authorization(self):
        """Verifies Pydantic schema validation and backend RBAC role enforcement on tools."""
        # 1. Invalid input schema validation
        inv_res = ToolRegistry.execute("get_inventory", {"limit": 9999})  # limit exceeds le=100
        self.assertFalse(inv_res.success)
        self.assertIn("Invalid arguments", inv_res.error)

        # 2. Authorization check: Cashier trying to run a manager/admin-only tool
        cashier_ctx = ToolContext(user_id=3, user_role=ROLE_CASHIER)
        unauth_res = ToolRegistry.execute("dummy_consequential_tool", {"message": "hello"}, context=cashier_ctx)
        self.assertFalse(unauth_res.success)
        self.assertIn("Unauthorized", unauth_res.error)

        # 3. Manager successfully runs tool
        mgr_ctx = ToolContext(user_id=2, user_role=ROLE_MANAGER)
        auth_res = ToolRegistry.execute("dummy_consequential_tool", {"message": "hello"}, context=mgr_ctx)
        self.assertTrue(auth_res.success)
        self.assertEqual(auth_res.data, "Executed: hello")

    def test_tool_idempotency_prevention(self):
        """Verifies idempotency key caches result and prevents duplicate action execution."""
        key = "idemp_test_key_123"
        ctx = ToolContext(user_id=1, user_role=ROLE_ADMIN, idempotency_key=key)

        res1 = ToolRegistry.execute("dummy_consequential_tool", {"message": "Action 1"}, context=ctx)
        self.assertTrue(res1.success)

        # Re-executing with the same key returns cached result
        res2 = ToolRegistry.execute("dummy_consequential_tool", {"message": "Action 2"}, context=ctx)
        self.assertTrue(res2.success)
        self.assertEqual(res2.data, "Executed: Action 1")

    def test_task_state_lifecycle_and_step_persistence(self):
        """Verifies TaskManager task creation, step tracing, approval request, and audit logging."""
        task_id = TaskManager.create_task(
            objective="Test weekly inventory replenishment under ₹10,000",
            user_id=1,
            constraints={"budget_limit_inr": 10000.0, "days_horizon": 7}
        )
        self.assertIsNotNone(task_id)

        # Record a step
        step_id = TaskManager.add_task_step(
            task_id=task_id,
            step_number=1,
            agent_name="InventoryAgent",
            action_type="EXECUTE_TOOL",
            tool_name="get_inventory",
            tool_input={"low_stock_only": True},
            step_status=StepStatus.RUNNING
        )
        self.assertTrue(step_id > 0)

        # Complete step
        TaskManager.update_task_step(
            step_id=step_id,
            step_status=StepStatus.COMPLETED,
            tool_output={"count": 5},
            reflection="Found 5 low stock products.",
            duration_ms=45
        )

        # Request approval
        appr_id = TaskManager.request_approval(
            task_id=task_id,
            action_name="CREATE_PURCHASE_ORDER",
            proposed_payload={"supplier_id": 1, "total": 8500.0},
            justification="Stockout prevention",
            estimated_cost=8500.0,
            requested_by_agent="ProcurementAgent"
        )
        self.assertTrue(appr_id > 0)

        # Inspect task
        task = TaskManager.get_task(task_id)
        self.assertEqual(task["status"], TaskStatus.WAITING_FOR_APPROVAL.value)
        self.assertEqual(task["approval_status"], ApprovalStatus.PENDING.value)
        self.assertEqual(len(task["steps"]), 1)
        self.assertEqual(len(task["approvals"]), 1)

        # Resolve approval by admin
        decision = TaskManager.resolve_approval(task_id, appr_id, approved=True, user_id=1)
        self.assertEqual(decision["status"], "APPROVED")

        updated_task = TaskManager.get_task(task_id)
        self.assertEqual(updated_task["approval_status"], ApprovalStatus.APPROVED.value)

    def test_multi_agent_supervisor_execution(self):
        """Verifies SupervisorAgent interprets goal, coordinates agents, and generates approval gateway."""
        supervisor = SupervisorAgent()
        task = supervisor.execute_goal(
            objective="Prepare my store for the next 7 days under ₹15,000. Prevent stockouts and check suppliers.",
            user_id=1,
            user_role="manager"
        )

        self.assertIsNotNone(task)
        self.assertIn("steps", task)
        self.assertTrue(len(task["steps"]) >= 5)

        # Verify steps were executed by specialized agents
        agent_names = [s["agent_name"] for s in task["steps"]]
        self.assertIn("InventoryAgent", agent_names)
        self.assertIn("ForecastingAgent", agent_names)
        self.assertIn("SupplierAgent", agent_names)
        self.assertIn("ProcurementAgent", agent_names)

        # Verify constraints were parsed
        constraints = task["constraints"]
        self.assertEqual(constraints["days_horizon"], 7)
        self.assertEqual(constraints["budget_limit_inr"], 15000.0)

        # Verify approval gateway if purchase orders were drafted
        if task["approvals"]:
            self.assertEqual(task["status"], TaskStatus.WAITING_FOR_APPROVAL.value)
            first_appr = task["approvals"][0]
            self.assertIn("estimated_cost", first_appr)
            self.assertTrue(first_appr["estimated_cost"] <= 15000.0)

    def test_procurement_agent_budget_enforcement(self):
        """Verifies ProcurementAgent strictly trims purchase orders when exceeding budget."""
        procurement = ProcurementAgent()
        mock_supplier_recoms = [
            {
                "product_id": 1,
                "product_name": "Ponni Boiled Rice 25kg",
                "selected_supplier_id": 1,
                "supplier_name": "Chennai Koyambedu Agro Wholesalers",
                "unit_cost": 1350.0,
                "adjusted_order_qty": 10.0,  # 10 * 1350 = 13,500
                "lead_time_days": 2
            },
            {
                "product_id": 4,
                "product_name": "Aashirvaad Atta 5kg",
                "selected_supplier_id": 1,
                "supplier_name": "Chennai Koyambedu Agro Wholesalers",
                "unit_cost": 245.0,
                "adjusted_order_qty": 20.0,  # 20 * 245 = 4,900
                "lead_time_days": 2
            }
        ]

        # Total unadjusted spend ~ ₹18,400 + GST
        # Test with strict ₹10,000 budget
        plan = procurement.prepare_procurement_plan(
            supplier_recommendations=mock_supplier_recoms,
            budget_limit_inr=10000.0
        )

        b_analysis = plan["budget_analysis"]
        self.assertTrue(b_analysis["is_within_budget"])
        self.assertTrue(b_analysis["adjusted_total_spend_inr"] <= 10000.0)
        self.assertTrue(len(plan["draft_orders"]) > 0)


if __name__ == "__main__":
    unittest.main()
