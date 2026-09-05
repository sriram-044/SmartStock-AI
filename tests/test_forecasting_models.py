import unittest
from backend.ai.forecasting import DemandForecastModel, get_product_forecast

class TestForecastingModels(unittest.TestCase):
    def test_forecast_generation_and_model_comparison(self):
        """Verifies ML models (Moving Average, Linear Regression, Random Forest) evaluate and forecast."""
        # Product 4: Aashirvaad Atta 5kg (Has 180 days sales history)
        forecast_res = get_product_forecast(product_id=4)
        
        self.assertEqual(forecast_res["product_id"], 4)
        self.assertIn("selected_model", forecast_res)
        self.assertIn("forecast_1d", forecast_res)
        self.assertIn("forecast_7d", forecast_res)
        self.assertIn("forecast_30d", forecast_res)
        self.assertIn("confidence_score", forecast_res)
        self.assertIn("model_comparison", forecast_res)

        # Ensure non-negative predictions
        self.assertTrue(forecast_res["forecast_1d"] >= 0)
        self.assertTrue(forecast_res["forecast_7d"] >= 0)
        self.assertTrue(forecast_res["forecast_30d"] >= forecast_res["forecast_7d"])

        # Model comparison has at least 2 models
        models = forecast_res["model_comparison"]
        self.assertTrue(len(models) >= 2)
        print(f"\n[Test Forecast] Selected Model: {forecast_res['selected_model']} (MAE: {forecast_res['validation_mae']})")

if __name__ == "__main__":
    unittest.main()
