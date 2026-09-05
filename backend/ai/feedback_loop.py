from datetime import datetime
from typing import Dict, Any, List
from backend.database.db import get_db, transaction

def record_recommendation_outcome(
    recommendation_id: int,
    actual_sales_observed: float,
    outcome_notes: str = ""
) -> Dict[str, Any]:
    """
    Records post-decision performance of an AI recommendation, calculating forecast error
    and feeding validation back into the continuous learning system.
    """
    with transaction() as conn:
        cur = conn.execute("SELECT * FROM ai_recommendations WHERE id = ?", (recommendation_id,))
        recom = cur.fetchone()
        if not recom:
            raise ValueError(f"Recommendation ID {recommendation_id} not found.")

        predicted_qty = float(recom["recommended_qty"])
        forecast_error = round(actual_sales_observed - predicted_qty, 2)
        pct_error = round((abs(forecast_error) / max(1.0, predicted_qty)) * 100.0, 1)

        conn.execute(
            """
            INSERT INTO ai_feedback_log (
                recommendation_id, product_id, predicted_demand,
                actual_sales_period, forecast_error, outcome_notes, logged_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                recommendation_id,
                recom["product_id"],
                predicted_qty,
                actual_sales_observed,
                forecast_error,
                outcome_notes or f"Error: {forecast_error:+.1f} units ({pct_error}%)"
            )
        )

        return {
            "recommendation_id": recommendation_id,
            "predicted_demand": predicted_qty,
            "actual_sales": actual_sales_observed,
            "forecast_error": forecast_error,
            "percentage_error": pct_error
        }

def get_feedback_metrics() -> Dict[str, Any]:
    """Computes overall AI recommendation accuracy and historical error trends."""
    conn = get_db()
    try:
        cur = conn.execute(
            """
            SELECT COUNT(*) as total_evaluated,
                   AVG(ABS(forecast_error)) as mean_absolute_error,
                   AVG(CASE WHEN predicted_demand > 0 THEN (ABS(forecast_error) / predicted_demand) * 100 ELSE 0 END) as mape
            FROM ai_feedback_log
            """
        )
        row = cur.fetchone()
        
        hist_cur = conn.execute(
            """
            SELECT fl.*, p.name as product_name, p.tamil_name, p.unit
            FROM ai_feedback_log fl
            JOIN products p ON fl.product_id = p.id
            ORDER BY fl.id DESC LIMIT 20
            """
        )
        history = [dict(r) for r in hist_cur.fetchall()]

        mae = round(row["mean_absolute_error"] or 0.0, 2)
        mape = round(row["mape"] or 0.0, 1)
        accuracy = max(0.0, round(100.0 - mape, 1))

        return {
            "total_evaluated_cycles": row["total_evaluated"],
            "mean_absolute_error": mae,
            "mean_absolute_percentage_error": mape,
            "overall_accuracy_pct": accuracy,
            "history": history
        }
    finally:
        conn.close()
