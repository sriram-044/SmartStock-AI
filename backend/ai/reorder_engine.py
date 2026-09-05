import math
from typing import Dict, Any, List, Optional
from backend.database.db import get_db
from backend.ai.forecasting import get_product_forecast

class ReorderEngine:
    """
    Intelligent inventory reorder engine implementing statistical safety stock,
    lead-time demand forecasting, stockout probability, and transparent formula breakdown.
    """

    def __init__(self, product_id: int):
        self.product_id = product_id

    def evaluate(self) -> Dict[str, Any]:
        """Runs full reorder evaluation for the product."""
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT p.*, i.current_stock, i.reserved_stock,
                       s.id as supplier_id, s.name as supplier_name, s.avg_lead_time_days,
                       s.reliability_score, s.rating
                FROM products p
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.id = ?
                """,
                (self.product_id,)
            )
            p = cur.fetchone()
            if not p:
                raise ValueError(f"Product {self.product_id} not found.")

            current_stock = float(p["current_stock"])
            lead_time_days = int(p["avg_lead_time_days"] or 3)
            min_stock = float(p["min_stock"])
            max_stock = float(p["max_stock"])

            # 1. Run Demand Forecast
            forecast_data = get_product_forecast(self.product_id)
            avg_daily_sales = max(0.2, float(forecast_data["avg_daily_sales"]))
            
            # Historical daily sales standard deviation (sigma_D)
            std_cur = conn.execute(
                """
                SELECT COALESCE(SUM(si.quantity), 0.0) as daily_qty
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE si.product_id = ? AND DATE(s.created_at) >= DATE('now', '-30 days')
                GROUP BY DATE(s.created_at)
                """,
                (self.product_id,)
            )
            daily_vals = [r["daily_qty"] for r in std_cur.fetchall()]
            if len(daily_vals) > 1:
                mean_d = sum(daily_vals) / len(daily_vals)
                variance_d = sum((x - mean_d) ** 2 for x in daily_vals) / (len(daily_vals) - 1)
                sigma_d = math.sqrt(variance_d)
            else:
                sigma_d = avg_daily_sales * 0.4

            # 2. Days of Inventory Remaining
            days_remaining = round(current_stock / avg_daily_sales, 1)

            # 3. Dynamic Safety Stock (Statistical approach: 95% service level -> Z = 1.65)
            # Safety Stock = Z * sigma_D * sqrt(LeadTime)
            z_factor = 1.65
            computed_safety_stock = math.ceil(z_factor * sigma_d * math.sqrt(lead_time_days))
            configured_safety_stock = int(p["safety_stock"] or 10)
            safety_stock = max(computed_safety_stock, configured_safety_stock)

            # 4. Expected Lead-Time Demand (LTD)
            lead_time_demand = round(avg_daily_sales * lead_time_days, 1)

            # 5. Target Inventory Level
            target_stock = round(lead_time_demand + safety_stock, 1)

            # 6. Recommended Reorder Quantity
            raw_reorder = target_stock - current_stock
            
            # 7. Risk Level Assessment
            if current_stock <= 0:
                risk_level = "CRITICAL"
                status_label = "Stockout (Immediate Delivery Needed)"
            elif days_remaining <= (lead_time_days * 0.7):
                risk_level = "CRITICAL"
                status_label = "Critical Stockout Risk"
            elif days_remaining <= lead_time_days:
                risk_level = "REORDER_NOW"
                status_label = "Reorder Now (Lead Time Breach Risk)"
            elif current_stock <= (target_stock * 0.8):
                risk_level = "REORDER_SOON"
                status_label = "Reorder Soon"
            elif current_stock > (max_stock * 1.2):
                risk_level = "SAFE"
                status_label = "Overstocked"
            else:
                risk_level = "SAFE"
                status_label = "Optimal Stock"

            # 8. Supplier Intelligence & Selection
            supplier_eval = self._evaluate_suppliers(conn, risk_level, lead_time_days, p["purchase_price"])
            chosen_supplier = supplier_eval["best_supplier"]
            
            # Adjust reorder quantity based on chosen supplier MOQ and pack size
            moq = chosen_supplier.get("moq", 1) if chosen_supplier else 1
            if raw_reorder > 0:
                recommended_qty = math.ceil(max(raw_reorder, moq))
                action = "Reorder"
            else:
                recommended_qty = 0
                action = "Monitor Stock"

            # 9. Formulate Clear Transparent Explanation
            if risk_level in ["CRITICAL", "REORDER_NOW"]:
                rationale = (
                    f"Current stock of {current_stock} {p['unit']} covers only ~{days_remaining} days of demand at "
                    f"{avg_daily_sales} {p['unit']}/day. The preferred supplier ({chosen_supplier.get('name', 'Wholesaler')}) "
                    f"requires {chosen_supplier.get('delivery_time_days', lead_time_days)} days for fulfillment. "
                    f"Without an immediate reorder of {recommended_qty} {p['unit']}, a stockout will occur before delivery."
                )
            elif risk_level == "REORDER_SOON":
                rationale = (
                    f"Stock level ({current_stock} {p['unit']}) is approaching the safety threshold ({safety_stock} {p['unit']}). "
                    f"Recommended order of {recommended_qty} {p['unit']} maintains target buffer of {target_stock} units."
                )
            else:
                rationale = (
                    f"Current inventory ({current_stock} {p['unit']}) comfortably satisfies expected demand "
                    f"over the supplier's {lead_time_days}-day lead time. Estimated {days_remaining} days of supply available."
                )

            # Formula Breakdown JSON
            formula_breakdown = {
                "product_name": p["name"],
                "unit": p["unit"],
                "current_stock": current_stock,
                "average_daily_sales": avg_daily_sales,
                "supplier_lead_time_days": chosen_supplier.get("delivery_time_days", lead_time_days) if chosen_supplier else lead_time_days,
                "lead_time_demand": lead_time_demand,
                "statistical_safety_stock": computed_safety_stock,
                "effective_safety_stock": safety_stock,
                "target_inventory": target_stock,
                "unadjusted_reorder": round(max(0.0, raw_reorder), 1),
                "supplier_moq": moq,
                "final_recommended_order": recommended_qty,
                "days_remaining": days_remaining,
                "formula_expression": "Recommended Reorder = MAX(Target Stock [LTD + Safety Stock] - Current Stock, MOQ)"
            }

            return {
                "product_id": self.product_id,
                "product_name": p["name"],
                "tamil_name": p["tamil_name"],
                "unit": p["unit"],
                "current_stock": current_stock,
                "days_remaining": days_remaining,
                "risk_level": risk_level,
                "status_label": status_label,
                "recommended_action": action,
                "recommended_qty": recommended_qty,
                "forecast_7d": forecast_data["forecast_7d"],
                "forecast_30d": forecast_data["forecast_30d"],
                "best_supplier": chosen_supplier,
                "supplier_options": supplier_eval["all_options"],
                "rationale": rationale,
                "formula_breakdown": formula_breakdown
            }
        finally:
            conn.close()

    def _evaluate_suppliers(self, conn, risk_level: str, default_lead_time: int, base_cost: float) -> Dict[str, Any]:
        """
        Ranks suppliers supplying this product based on:
        - Delivery speed (urgency weighted heavily if CRITICAL)
        - Purchase price
        - Supplier reliability score
        - Minimum order quantity (MOQ)
        """
        cur = conn.execute(
            """
            SELECT sp.supplier_price, sp.moq, sp.delivery_time_days,
                   s.id as supplier_id, s.name, s.rating, s.reliability_score, s.return_rate,
                   s.district, s.city
            FROM supplier_products sp
            JOIN suppliers s ON sp.supplier_id = s.id
            WHERE sp.product_id = ?
            """,
            (self.product_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            # Fallback to preferred supplier from products table
            cur_p = conn.execute(
                """
                SELECT s.id as supplier_id, s.name, s.avg_lead_time_days as delivery_time_days,
                       s.reliability_score, s.rating, s.district, s.city
                FROM products p
                JOIN suppliers s ON p.preferred_supplier_id = s.id
                WHERE p.id = ?
                """,
                (self.product_id,)
            )
            fallback = cur_p.fetchone()
            if fallback:
                f_dict = dict(fallback)
                f_dict["supplier_price"] = base_cost
                f_dict["moq"] = 1
                rows = [f_dict]
            else:
                return {"best_supplier": None, "all_options": []}

        # Multi-attribute scoring
        # If CRITICAL: Lead time weight = 0.50, Reliability = 0.30, Price = 0.20
        # If SAFE/MONITOR: Price weight = 0.50, Reliability = 0.30, Lead time = 0.20
        if risk_level in ["CRITICAL", "REORDER_NOW"]:
            w_lead, w_rel, w_price = 0.50, 0.30, 0.20
        else:
            w_lead, w_rel, w_price = 0.20, 0.30, 0.50

        min_lead = min(r["delivery_time_days"] for r in rows)
        min_price = min(r["supplier_price"] for r in rows)

        scored_suppliers = []
        for s in rows:
            # Normalized scores between 0 and 100
            lead_score = (min_lead / max(1, s["delivery_time_days"])) * 100.0
            price_score = (min_price / max(1.0, s["supplier_price"])) * 100.0
            rel_score = float(s["reliability_score"] or 90.0)

            composite_score = round((lead_score * w_lead) + (rel_score * w_rel) + (price_score * w_price), 1)
            
            s["composite_score"] = composite_score
            s["lead_time_score"] = round(lead_score, 1)
            s["price_score"] = round(price_score, 1)
            scored_suppliers.append(s)

        scored_suppliers.sort(key=lambda x: x["composite_score"], reverse=True)
        best = scored_suppliers[0]

        # Attach reason why chosen
        if risk_level in ["CRITICAL", "REORDER_NOW"] and best["delivery_time_days"] == min_lead:
            best["selection_reason"] = (
                f"Selected for fastest delivery ({best['delivery_time_days']} days) and high reliability "
                f"({best['reliability_score']}%) to prevent immediate stockout."
            )
        else:
            best["selection_reason"] = (
                f"Selected for best balance of competitive price (₹{best['supplier_price']}) and proven reliability "
                f"({best['reliability_score']}%)."
            )

        return {
            "best_supplier": best,
            "all_options": scored_suppliers
        }
