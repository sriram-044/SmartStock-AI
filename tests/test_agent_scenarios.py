import unittest
from backend.ai.agents.supervisor_agent import SupervisorAgent
from backend.ai.agents.expiry_agent import ExpiryAgent
from backend.ai.agents.supplier_agent import SupplierAgent
from backend.ai.agents.procurement_agent import ProcurementAgent
from backend.ai.task_state import TaskManager, TaskStatus, ApprovalStatus
from backend.ai.tool_registry import ToolRegistry, ToolContext
from backend.auth.roles import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER


class TestEndToEndAgentScenarios(unittest.TestCase):
    """
    Validates all 7 End-to-End Acceptance Scenarios required by Section 18.
    """

    def setUp(self):
        self.supervisor = SupervisorAgent()

    def test_scenario_1_inventory_planning_3_days(self):
        """Scenario 1: Find products likely to run out within 3 days and prepare a replenishment plan."""
        task = self.supervisor.execute_goal(
            objective="Find products likely to run out within three days and prepare a replenishment plan.",
            user_id=1,
            user_role="manager"
        )

        self.assertIsNotNone(task)
        self.assertEqual(task["constraints"]["days_horizon"], 3)
        self.assertTrue(len(task["steps"]) >= 4)

        final_out = task.get("final_output", {})
        self.assertIn("inventory_analysis", final_out)
        self.assertIn("forecasts", final_out)

        inv_data = final_out["inventory_analysis"]
        self.assertTrue(inv_data["scanned_products"] > 0)
        self.assertIn("critical_stockouts", inv_data)
        self.assertIn("reorder_needed", inv_data)

    def test_scenario_2_budget_constrained_procurement(self):
        """Scenario 2: Prepare a restocking plan under ₹10,000."""
        task = self.supervisor.execute_goal(
            objective="Prepare a restocking plan under ₹10,000.",
            user_id=1,
            user_role="manager"
        )

        self.assertIsNotNone(task)
        self.assertEqual(task["constraints"]["budget_limit_inr"], 10000.0)

        final_out = task.get("final_output", {})
        proc_plan = final_out.get("procurement_plan", {})
        b_analysis = proc_plan.get("budget_analysis", {})

        # Budget ceiling must be respected
        self.assertTrue(b_analysis["is_within_budget"])
        spend = b_analysis.get("adjusted_total_spend_inr", b_analysis.get("total_spend_inr", 0.0))
        self.assertTrue(spend <= 10000.0)

        # Requires human approval
        self.assertEqual(task["status"], TaskStatus.WAITING_FOR_APPROVAL.value)
        self.assertTrue(len(task["approvals"]) > 0)

    def test_scenario_3_supplier_delivery_constraint(self):
        """Scenario 3: Restock the products that will run out before the preferred supplier can deliver."""
        supplier_agent = SupplierAgent()
        # Item with 2 days remaining, preferred supplier lead time is 4 days
        urgent_items = [
            {
                "product_id": 4, # Aashirvaad Atta
                "name": "Aashirvaad Shudh Chakki Atta 5kg",
                "days_remaining": 2.0,
                "recommended_qty": 15.0
            }
        ]

        eval_res = supplier_agent.evaluate_suppliers_for_products(urgent_items)
        self.assertTrue(len(eval_res["product_recommendations"]) > 0)
        first_recom = eval_res["product_recommendations"][0]

        # Verified real supplier records were returned
        self.assertIsNotNone(first_recom["selected_supplier_id"])
        self.assertTrue(first_recom["lead_time_days"] > 0)
        self.assertTrue(first_recom["unit_cost"] > 0)
        self.assertIn("tradeoff_notes", first_recom)

    def test_scenario_4_expiry_prevention_and_markdown(self):
        """Scenario 4: Identify products likely to expire before they sell and suggest corrective actions."""
        expiry_agent = ExpiryAgent()
        res = expiry_agent.evaluate_expiry_risks(days_window=45)

        self.assertIn("total_expiring_batches", res)
        self.assertIn("total_at_risk_inr", res)
        self.assertTrue(res["total_expiring_batches"] > 0)
        self.assertTrue(res["total_at_risk_inr"] > 0)

        # Ensure recommendations never suggest selling expired items
        for batch in res["all_batches"]:
            if batch["days_to_expiry"] < 0:
                self.assertEqual(batch["risk_status"], "EXPIRED")
                self.assertIn("Do NOT sell", batch["recommended_action"])
            else:
                self.assertIn("recommended_action", batch)

    def test_scenario_5_tool_failure_handling(self):
        """Scenario 5: Simulate tool failure without inventing data."""
        # Non-existent product ID
        invalid_res = ToolRegistry.execute("calculate_stockout_risk", {"product_id": 999999})
        self.assertFalse(invalid_res.success)
        self.assertIn("not found", invalid_res.error.lower())

        # Missing required parameter
        missing_res = ToolRegistry.execute("get_product_details", {})
        self.assertFalse(missing_res.success)
        self.assertIn("Invalid arguments", missing_res.error)

    def test_scenario_6_approval_enforcement(self):
        """Scenario 6: Attempt to execute purchase order without approval."""
        # 1. Cashier attempts to call submit_approved_purchase_order directly
        cashier_ctx = ToolContext(user_id=3, user_role=ROLE_CASHIER)
        res = ToolRegistry.execute(
            "submit_approved_purchase_order",
            {"supplier_id": 1, "items": [{"product_id": 1, "quantity": 10.0, "unit_cost": 1350.0}]},
            context=cashier_ctx
        )
        self.assertFalse(res.success)
        self.assertIn("Unauthorized", res.error)

        # 2. Cashier attempts to approve a task
        task = self.supervisor.execute_goal(
            objective="Prepare restock under ₹5,000",
            user_id=3,
            user_role="cashier"
        )
        if task.get("approvals"):
            appr_id = task["approvals"][0]["id"]
            with self.assertRaises(PermissionError):
                self.supervisor.process_approval_decision(
                    task_id=task["id"],
                    approval_id=appr_id,
                    approved=True,
                    user_id=3,
                    user_role="cashier"
                )

    def test_scenario_7_result_verification(self):
        """Scenario 7: Verified order creation upon authorized approval."""
        task = self.supervisor.execute_goal(
            objective="Prepare restocking plan under ₹12,000",
            user_id=1,
            user_role="admin"
        )

        if task.get("approvals"):
            appr_id = task["approvals"][0]["id"]
            # Admin approves
            approval_result = self.supervisor.process_approval_decision(
                task_id=task["id"],
                approval_id=appr_id,
                approved=True,
                user_id=1,
                user_role="admin",
                reason="Weekly replenishment approved"
            )

            self.assertEqual(approval_result["status"], "COMPLETED")
            exec_res = approval_result["execution_result"]
            self.assertTrue(exec_res["success"])
            self.assertTrue(exec_res["verified"])
            self.assertIsNotNone(exec_res["po_number"])

            # Verify PO exists in DB
            ver = ToolRegistry.execute("verify_purchase_order", {"po_number": exec_res["po_number"]})
            self.assertTrue(ver.success)
            self.assertTrue(ver.data["verified"])
            self.assertEqual(ver.data["status"], "ORDERED")


if __name__ == "__main__":
    unittest.main()
