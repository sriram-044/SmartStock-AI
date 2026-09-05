import unittest
from backend.ai.reorder_engine import ReorderEngine
from backend.ai.dead_stock_engine import analyze_dead_and_slow_stock
from backend.ai.expiry_engine import evaluate_expiry_risks

class TestReorderAndSuppliers(unittest.TestCase):
    def test_reorder_formula_breakdown(self):
        """Verifies safety stock, lead-time demand, and transparent formula components."""
        # Product 41: Clinic Plus Shampoo 340ml (Critical stockout situation)
        engine = ReorderEngine(41)
        res = engine.evaluate()

        self.assertIn(res["risk_level"], ["CRITICAL", "REORDER_NOW"])
        self.assertIn("formula_breakdown", res)
        fb = res["formula_breakdown"]
        
        self.assertIn("lead_time_demand", fb)
        self.assertIn("effective_safety_stock", fb)
        self.assertIn("target_inventory", fb)
        self.assertIn("final_recommended_order", fb)
        self.assertTrue(res["recommended_qty"] > 0)
        self.assertIsNotNone(res["best_supplier"])

    def test_dead_stock_detection(self):
        """Verifies dead stock detection and blocked capital computation."""
        dead_stock = analyze_dead_and_slow_stock(days_threshold=45)
        self.assertTrue(len(dead_stock) > 0)
        first_item = dead_stock[0]
        self.assertIn("blocked_capital", first_item)
        self.assertTrue(first_item["blocked_capital"] > 0)
        self.assertIn(first_item["classification"], ["DEAD_STOCK", "SLOW_MOVING"])

    def test_fefo_expiry_evaluation(self):
        """Verifies FEFO batch risk assessment and markdown recommendation."""
        expiry_items = evaluate_expiry_risks(days_window=45)
        self.assertTrue(len(expiry_items) > 0)
        for it in expiry_items:
            self.assertTrue(it["days_to_expiry"] <= 45)
            self.assertIn("potential_loss_inr", it)
            self.assertIn("recommended_action", it)

if __name__ == "__main__":
    unittest.main()
