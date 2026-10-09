from typing import Dict, Any, Optional
from backend.ai.feedback_loop import get_feedback_metrics, record_recommendation_outcome


class FeedbackAgent:
    """
    Specialized Feedback & Continuous Evaluation Agent.
    Tracks prediction errors, computes Mean Absolute Error (MAE),
    and evaluates recommendation acceptance rates across operational cycles.
    """

    name = "FeedbackAgent"

    def record_outcome(
        self,
        recommendation_id: int,
        actual_sales_observed: float,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Records ground-truth sales outcome to measure forecast error."""
        return record_recommendation_outcome(
            recommendation_id=recommendation_id,
            actual_sales_observed=actual_sales_observed,
            outcome_notes=notes
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """Calculates system-wide AI recommendation accuracy and historical performance."""
        metrics = get_feedback_metrics()
        return {
            "agent": self.name,
            "metrics": metrics,
            "summary": (
                f"Continuous Feedback: Evaluated {metrics.get('total_evaluated_cycles', 0)} cycles. "
                f"Average Forecast Error: {metrics.get('average_forecast_error', 0.0)} units."
            )
        }
