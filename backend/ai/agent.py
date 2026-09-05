import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.database.db import get_db, transaction
from backend.ai.reorder_engine import ReorderEngine
from backend.services.purchase_service import create_purchase_order

class InventoryAgent:
    """
    Central Agentic AI Orchestrator implementing the full Observe-Analyze-Forecast-Reason-Decide loop,
    creating transparent recommendation cards and managing the Human-In-The-Loop approval cycle.
    """

    def run_cycle(self) -> Dict[str, Any]:
        """
        Executes a full scan cycle across all active inventory items:
        1. Observe stock levels and recent sales
        2. Analyze lead times and safety thresholds
        3. Forecast future demand using ML models
        4. Identify risk levels
        5. Formulate transparent reorder proposals
        6. Persist recommendations into ai_recommendations table
        """
        conn = get_db()
        try:
            cur = conn.execute("SELECT id, name FROM products WHERE is_active = 1")
            products = cur.fetchall()
            
            created_count = 0
            critical_count = 0
            recommendations_summary = []

            for p in products:
                prod_id = p["id"]
                engine = ReorderEngine(prod_id)
                eval_res = engine.evaluate()
                risk_level = eval_res["risk_level"]

                if risk_level in ["CRITICAL", "REORDER_NOW", "REORDER_SOON"]:
                    if risk_level == "CRITICAL":
                        critical_count += 1
                        
                    # Check if there is already an active pending recommendation
                    pend_cur = conn.execute(
                        "SELECT id FROM ai_recommendations WHERE product_id = ? AND status = 'PENDING'",
                        (prod_id,)
                    )
                    existing = pend_cur.fetchone()

                    best_sup = eval_res.get("best_supplier")
                    sup_id = best_sup.get("supplier_id") if best_sup else None
                    formula_json = json.dumps(eval_res["formula_breakdown"])

                    if existing:
                        # Update existing pending recommendation
                        conn.execute(
                            """
                            UPDATE ai_recommendations SET
                                risk_level = ?, recommended_action = ?, recommended_qty = ?,
                                suggested_supplier_id = ?, rationale = ?,
                                transparent_formula_json = ?, created_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (
                                risk_level,
                                eval_res["recommended_action"],
                                eval_res["recommended_qty"],
                                sup_id,
                                eval_res["rationale"],
                                formula_json,
                                existing["id"]
                            )
                        )
                        recom_id = existing["id"]
                    else:
                        # Insert new recommendation
                        ins_cur = conn.execute(
                            """
                            INSERT INTO ai_recommendations (
                                product_id, risk_level, recommended_action, recommended_qty,
                                suggested_supplier_id, rationale, transparent_formula_json, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
                            """,
                            (
                                prod_id,
                                risk_level,
                                eval_res["recommended_action"],
                                eval_res["recommended_qty"],
                                sup_id,
                                eval_res["rationale"],
                                formula_json
                            )
                        )
                        recom_id = ins_cur.lastrowid
                        created_count += 1

                    recommendations_summary.append({
                        "recommendation_id": recom_id,
                        "product_name": p["name"],
                        "risk_level": risk_level,
                        "recommended_qty": eval_res["recommended_qty"],
                        "supplier": best_sup.get("name") if best_sup else "None"
                    })

            conn.commit()
            return {
                "scan_time": datetime.now().isoformat(),
                "products_scanned": len(products),
                "new_or_updated_recommendations": created_count,
                "critical_risks_detected": critical_count,
                "summary": recommendations_summary
            }
        finally:
            conn.close()

    def list_recommendations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists AI recommendations with product details, formulas, and supplier info."""
        conn = get_db()
        try:
            query = """
                SELECT ar.*, p.name as product_name, p.tamil_name, p.unit, p.selling_price,
                       p.purchase_price, p.gst_rate, i.current_stock,
                       s.name as supplier_name, s.phone as supplier_phone,
                       s.reliability_score as supplier_reliability,
                       s.avg_lead_time_days as supplier_lead_time,
                       u.full_name as decision_by_name
                FROM ai_recommendations ar
                JOIN products p ON ar.product_id = p.id
                JOIN inventory i ON p.id = i.product_id
                LEFT JOIN suppliers s ON ar.suggested_supplier_id = s.id
                LEFT JOIN users u ON ar.user_decision_by = u.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND ar.status = ?"
                params.append(status)
            query += " ORDER BY CASE ar.risk_level WHEN 'CRITICAL' THEN 1 WHEN 'REORDER_NOW' THEN 2 WHEN 'REORDER_SOON' THEN 3 ELSE 4 END, ar.id DESC"
            cur = conn.execute(query, params)
            rows = [dict(r) for r in cur.fetchall()]

            for r in rows:
                if r.get("transparent_formula_json"):
                    try:
                        r["formula_breakdown"] = json.loads(r["transparent_formula_json"])
                    except Exception:
                        r["formula_breakdown"] = {}
                else:
                    r["formula_breakdown"] = {}
            return rows
        finally:
            conn.close()

    def approve_recommendation(self, recommendation_id: int, user_id: int) -> Dict[str, Any]:
        """
        Human-in-the-loop: Approves an AI recommendation.
        Automatically creates a draft Purchase Order with the recommended supplier and quantity.
        """
        product_id = None
        supplier_id = None
        qty = 0.0
        unit_cost = 100.0
        gst_rate = 5.0

        with transaction() as conn:
            cur = conn.execute("SELECT * FROM ai_recommendations WHERE id = ?", (recommendation_id,))
            recom = cur.fetchone()
            if not recom:
                raise ValueError(f"Recommendation ID {recommendation_id} not found.")
            if recom["status"] != "PENDING":
                raise ValueError(f"Recommendation is already {recom['status']}.")

            product_id = recom["product_id"]
            supplier_id = recom["suggested_supplier_id"]
            qty = float(recom["recommended_qty"])

            # Mark recommendation as APPROVED
            conn.execute(
                """
                UPDATE ai_recommendations SET
                    status = 'APPROVED', approved_qty = ?, user_decision_by = ?,
                    decision_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (qty, user_id, recommendation_id)
            )

            # Look up purchase price
            p_cur = conn.execute("SELECT purchase_price, gst_rate FROM products WHERE id = ?", (product_id,))
            p_row = p_cur.fetchone()
            if p_row:
                unit_cost = float(p_row["purchase_price"])
                gst_rate = float(p_row["gst_rate"])

        # Auto-create Purchase Order outside the previous transaction to avoid database locks
        po_number = None
        if supplier_id and qty > 0:
            po = create_purchase_order(
                data={
                    "supplier_id": supplier_id,
                    "invoice_number": f"AI-RECOM-{recommendation_id}",
                    "items": [{
                        "product_id": product_id,
                        "quantity": qty,
                        "unit_cost": unit_cost,
                        "gst_rate": gst_rate
                    }]
                },
                user_id=user_id
            )
            po_number = po["po_number"]

        return {
            "recommendation_id": recommendation_id,
            "status": "APPROVED",
            "approved_qty": qty,
            "generated_po_number": po_number
        }

    def modify_and_approve(self, recommendation_id: int, new_quantity: float, user_id: int) -> Dict[str, Any]:
        """
        Human-in-the-loop: Modifies recommended quantity before approving.
        Generates Purchase Order with the shopkeeper's adjusted quantity.
        """
        product_id = None
        supplier_id = None
        unit_cost = 100.0
        gst_rate = 5.0

        with transaction() as conn:
            cur = conn.execute("SELECT * FROM ai_recommendations WHERE id = ?", (recommendation_id,))
            recom = cur.fetchone()
            if not recom:
                raise ValueError(f"Recommendation ID {recommendation_id} not found.")

            product_id = recom["product_id"]
            supplier_id = recom["suggested_supplier_id"]

            conn.execute(
                """
                UPDATE ai_recommendations SET
                    status = 'MODIFIED', approved_qty = ?, user_decision_by = ?,
                    decision_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_quantity, user_id, recommendation_id)
            )

            p_cur = conn.execute("SELECT purchase_price, gst_rate FROM products WHERE id = ?", (product_id,))
            p_row = p_cur.fetchone()
            if p_row:
                unit_cost = float(p_row["purchase_price"])
                gst_rate = float(p_row["gst_rate"])

        # Auto-create PO outside transaction
        po_number = None
        if supplier_id and new_quantity > 0:
            po = create_purchase_order(
                data={
                    "supplier_id": supplier_id,
                    "invoice_number": f"AI-MOD-{recommendation_id}",
                    "items": [{
                        "product_id": product_id,
                        "quantity": new_quantity,
                        "unit_cost": unit_cost,
                        "gst_rate": gst_rate
                    }]
                },
                user_id=user_id
            )
            po_number = po["po_number"]

        return {
            "recommendation_id": recommendation_id,
            "status": "MODIFIED",
            "approved_qty": new_quantity,
            "generated_po_number": po_number
        }

    def reject_recommendation(self, recommendation_id: int, user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """Human-in-the-loop: Rejects an AI recommendation with recorded justification."""
        with transaction() as conn:
            cur = conn.execute("SELECT id, status FROM ai_recommendations WHERE id = ?", (recommendation_id,))
            recom = cur.fetchone()
            if not recom:
                raise ValueError(f"Recommendation ID {recommendation_id} not found.")

            conn.execute(
                """
                UPDATE ai_recommendations SET
                    status = 'REJECTED', user_decision_by = ?, decision_at = CURRENT_TIMESTAMP,
                    rationale = rationale || ?
                WHERE id = ?
                """,
                (user_id, f" [Rejected by User: {reason or 'Shopkeeper override'}]", recommendation_id)
            )
            return {
                "recommendation_id": recommendation_id,
                "status": "REJECTED",
                "reason": reason
            }
