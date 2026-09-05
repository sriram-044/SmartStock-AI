import unittest
from backend.ai.agent import InventoryAgent
from backend.ai.chat_assistant import NaturalLanguageAssistant
from backend.ai.feedback_loop import record_recommendation_outcome, get_feedback_metrics

class TestAgentAndAI(unittest.TestCase):
    def test_agentic_loop_and_human_in_the_loop_approval(self):
        """Verifies full Observe-Analyze-Decide loop, approval, and auto PO generation."""
        agent = InventoryAgent()
        cycle_res = agent.run_cycle()
        self.assertTrue(cycle_res["products_scanned"] > 0)

        recoms = agent.list_recommendations(status="PENDING")
        self.assertTrue(len(recoms) > 0)
        first_recom = recoms[0]

        # Test approving recommendation
        approval_res = agent.approve_recommendation(first_recom["id"], user_id=1)
        self.assertEqual(approval_res["status"], "APPROVED")
        self.assertIsNotNone(approval_res["generated_po_number"])

    def test_natural_language_assistant_factual_queries(self):
        """Verifies conversational Q&A handles critical questions without fabricating."""
        # 1. Critical restock query
        res1 = NaturalLanguageAssistant.ask("Which products need immediate restocking?")
        self.assertIn("answer", res1)
        self.assertIn("tamil_summary", res1)
        self.assertIsNotNone(res1["data"])

        # 2. Blocked capital query
        res2 = NaturalLanguageAssistant.ask("How much inventory value is currently blocked in dead stock?")
        self.assertIn("blocked", res2["answer"].lower())

        # 3. Product inquiry
        res3 = NaturalLanguageAssistant.ask("Why is shampoo marked as critical?")
        self.assertIn("Clinic Plus", res3["answer"])

    def test_feedback_loop_and_accuracy_tracking(self):
        """Verifies feedback loop records forecast error and computes accuracy."""
        recom_id = 1
        res = record_recommendation_outcome(recom_id, actual_sales_observed=45.0, outcome_notes="Verified against POS sales")
        self.assertEqual(res["recommendation_id"], recom_id)
        self.assertIn("forecast_error", res)

        metrics = get_feedback_metrics()
        self.assertTrue(metrics["total_evaluated_cycles"] > 0)

if __name__ == "__main__":
    unittest.main()
