import re
from typing import Dict, Any, List, Optional
from backend.ai.tools import AgentTools

class NaturalLanguageAssistant:
    """
    Conversational assistant powered by database introspection tools.
    Parses intent, retrieves factual records, and synthesizes structured,
    non-hallucinatory responses in English with Tamil summaries.
    """

    @classmethod
    def ask(cls, query: str) -> Dict[str, Any]:
        q = query.lower().strip()

        # 1. Critical Restocking / Immediate restocking
        if any(term in q for term in ["restock", "restocking", "run out", "critical", "low stock"]):
            # Check if asking about a specific product, e.g. "Why is shampoo marked as critical?"
            prod_match = cls._extract_product_name(q)
            if prod_match and ("why" in q or "explain" in q):
                return cls._handle_explain_product(prod_match)
            return cls._handle_critical_restock()

        # 2. Dead stock / Not selling / Slow moving / Blocked capital
        if any(term in q for term in ["not selling", "dead stock", "slow moving", "blocked", "tied up", "capital"]):
            return cls._handle_dead_stock()

        # 3. Best supplier / Supplier comparison, e.g. "Which supplier is best for rice?"
        if "supplier" in q or "vendor" in q:
            prod_match = cls._extract_product_name(q) or "rice"
            return cls._handle_best_supplier(prod_match)

        # 4. Expiry questions, e.g. "Which products may expire within 30 days?"
        if any(term in q for term in ["expire", "expiry", "batch", "shelf life"]):
            return cls._handle_expiry(q)

        # 5. Best-selling / Top selling products
        if any(term in q for term in ["best-selling", "best selling", "top selling", "highest sales"]):
            return cls._handle_top_selling()

        # 6. High profit but low stock
        if any(term in q for term in ["profit", "margin"]) and any(term in q for term in ["low stock", "low", "restock"]):
            return cls._handle_high_profit_low_stock()

        # 7. Specific product lookup, e.g. "Stock of Aashirvaad Atta" or "Check Ponni rice"
        prod_match = cls._extract_product_name(q)
        if prod_match:
            return cls._handle_product_query(prod_match)

        # Generic default response with helpful sample prompts
        return {
            "query": query,
            "answer": (
                "I am your Indian Retail Inventory AI Assistant. You can ask me real-time questions such as:\n"
                "• 'Which products need immediate restocking?'\n"
                "• 'Why is shampoo marked as critical?'\n"
                "• 'Which products are not selling?'\n"
                "• 'Which supplier is best for rice?'\n"
                "• 'How much inventory value is currently blocked in dead stock?'\n"
                "• 'Which products may expire within 30 days?'\n"
                "• 'What were my best-selling products this month?'\n"
                "• 'Show products with high profit but low stock.'"
            ),
            "tamil_summary": "இருப்பு விவரங்கள், மறுஆர்டர் பரிந்துரைகள் மற்றும் காலாவதி பற்றிய கேள்விகளை நீங்கள் கேட்கலாம்.",
            "data": None
        }

    @classmethod
    def _handle_critical_restock(cls) -> Dict[str, Any]:
        items = AgentTools.get_critical_restock_list()
        if not items:
            return {
                "answer": "Great news! Currently, no products are at critical stockout risk. All inventory levels are above their respective safety buffers.",
                "tamil_summary": "அனைத்துப் பொருட்களின் இருப்பும் போதுமான அளவில் பாதுகாப்பாக உள்ளது.",
                "data": []
            }
        
        lines = ["Here are the products requiring immediate replenishment:"]
        for it in items[:6]:
            t_name = f" ({it['tamil_name']})" if it.get("tamil_name") else ""
            sup = f" | Supplier: {it['supplier_name']}" if it.get("supplier_name") else ""
            lines.append(f"• **{it['name']}{t_name}**: Current stock {it['current_stock']} {it['unit']} (Reorder Level: {it['reorder_level']}){sup}")

        return {
            "answer": "\n".join(lines),
            "tamil_summary": f"மொத்தம் {len(items)} பொருட்கள் குறைந்த அல்லது ஆபத்தான இருப்பில் உள்ளன. உடனடியாக மறுஆர்டர் செய்யவும்.",
            "data": items
        }

    @classmethod
    def _handle_explain_product(cls, prod_query: str) -> Dict[str, Any]:
        res = AgentTools.explain_product_reorder(prod_query)
        if "error" in res:
            return {
                "answer": res["error"],
                "tamil_summary": "பொருள் கண்டுபிடிக்கப்படவில்லை.",
                "data": None
            }

        fb = res.get("formula_breakdown", {})
        answer = (
            f"**Analysis for {res['product_name']}** ({res.get('tamil_name', '')}):\n"
            f"• **Risk Status**: {res['risk_level']} - {res['status_label']}\n"
            f"• **Current Stock**: {res['current_stock']} {res['unit']} (~{res['days_remaining']} days remaining)\n"
            f"• **Lead-Time Demand**: {fb.get('lead_time_demand', 0)} {res['unit']} during the {fb.get('supplier_lead_time_days', 3)}-day delivery window\n"
            f"• **Safety Buffer**: {fb.get('effective_safety_stock', 0)} {res['unit']}\n"
            f"• **Recommended Reorder**: **{res['recommended_qty']} {res['unit']}**\n\n"
            f"**Why this action was recommended**: {res['rationale']}"
        )
        tamil = f"{res['product_name']} இருப்பு {res['current_stock']} {res['unit']}. {res['days_remaining']} நாட்களில் காலியாகும் வாய்ப்புள்ளது. மறுஆர்டர் பரிந்துரை: {res['recommended_qty']} {res['unit']}."
        return {
            "answer": answer,
            "tamil_summary": tamil,
            "data": res
        }

    @classmethod
    def _handle_dead_stock(cls) -> Dict[str, Any]:
        res = AgentTools.get_dead_stock_summary()
        count = res["total_dead_stock_items"]
        blocked = res["total_blocked_capital_inr"]
        top_items = res["top_dead_items"]

        if count == 0:
            return {
                "answer": "No dead stock detected! All products are moving within normal retail velocity.",
                "tamil_summary": "முடங்கிய இருப்பு எதுவும் இல்லை. அனைத்துப் பொருட்களும் வழக்கமான வேகத்தில் விற்பனையாகின்றன.",
                "data": res
            }

        lines = [
            f"A total of **₹{blocked:,.2f}** in working capital is currently blocked across **{count} slow-moving/dead stock items**.",
            "Top items tying up capital:"
        ]
        for it in top_items[:5]:
            lines.append(f"• **{it['product_name']}**: {it['current_stock']} {it['unit']} idle for {it['days_idle']} days (₹{it['blocked_capital']:,.2f} blocked) → *{it['recommended_action']}*")

        return {
            "answer": "\n".join(lines),
            "tamil_summary": f"மொத்தம் ₹{blocked:,.2f} மூலதனம் விற்பனையாகாத பொருட்களில் முடங்கியுள்ளது.",
            "data": res
        }

    @classmethod
    def _handle_best_supplier(cls, prod_query: str) -> Dict[str, Any]:
        res = AgentTools.get_supplier_comparison(prod_query)
        if "error" in res:
            return {"answer": res["error"], "tamil_summary": "பொருள் கிடைக்கவில்லை.", "data": None}

        best = res.get("best_supplier")
        if not best:
            return {"answer": f"No registered suppliers found for {res['product']}.", "tamil_summary": "விநியோகஸ்தர் இல்லை.", "data": None}

        answer = (
            f"**Best Supplier for {res['product']}** ({res.get('tamil_name', '')}):\n"
            f"• **Supplier**: **{best['name']}** (Location: {best.get('district', 'Tamil Nadu')})\n"
            f"• **Price**: ₹{best.get('supplier_price', 0):,.2f} per {res['unit']}\n"
            f"• **Delivery Lead Time**: {best.get('delivery_time_days', 3)} days\n"
            f"• **Reliability Score**: {best.get('reliability_score', 95)}%\n"
            f"• **Reason**: {best.get('selection_reason', 'Optimal price and turnaround.')}"
        )
        tamil = f"{res['product']} கொள்முதலுக்கு சிறந்த விநியோகஸ்தர்: {best['name']} (விலை: ₹{best.get('supplier_price', 0)}, விநியோக காலம்: {best.get('delivery_time_days')} நாட்கள்)."
        return {"answer": answer, "tamil_summary": tamil, "data": res}

    @classmethod
    def _handle_expiry(cls, q: str) -> Dict[str, Any]:
        batches = AgentTools.get_expiring_batches(days=35)
        if not batches:
            return {
                "answer": "No products are expiring within the next 35 days. FEFO rotation is well-maintained.",
                "tamil_summary": "அடுத்த 35 நாட்களில் காலாவதியாகும் பொருட்கள் எதுவும் இல்லை.",
                "data": []
            }

        lines = [f"Found **{len(batches)} batches** expiring within 35 days:"]
        for b in batches[:5]:
            lines.append(
                f"• **{b['product_name']}** (Batch: {b['batch_number']}): {b['remaining_qty']} {b['unit']} "
                f"expires in **{b['days_to_expiry']} days**. Estimated unsold loss: **₹{b['potential_loss_inr']:,.2f}** "
                f"→ *{b['recommended_action']}*"
            )

        return {
            "answer": "\n".join(lines),
            "tamil_summary": f"அடுத்த 35 நாட்களில் {len(batches)} பொருட்கள் காலாவதியாகின்றன. தள்ளுபடி விற்பனை செய்ய பரிந்துரைக்கப்படுகிறது.",
            "data": batches
        }

    @classmethod
    def _handle_top_selling(cls) -> Dict[str, Any]:
        top = AgentTools.get_top_selling_products(limit=5)
        if not top:
            return {"answer": "No sales transactions recorded in the past 30 days.", "tamil_summary": "விற்பனை பதிவுகள் இல்லை.", "data": []}

        lines = ["**Top 5 Best-Selling Products This Month:**"]
        for idx, it in enumerate(top, 1):
            lines.append(f"{idx}. **{it['name']}**: {it['units_sold']} {it['unit']} sold (Revenue: ₹{it['revenue']:,.2f})")

        return {
            "answer": "\n".join(lines),
            "tamil_summary": f"அதிகம் விற்பனையான முன்னணி பொருட்கள் பட்டியலிடப்பட்டுள்ளன.",
            "data": top
        }

    @classmethod
    def _handle_high_profit_low_stock(cls) -> Dict[str, Any]:
        items = AgentTools.get_high_profit_low_stock()
        if not items:
            return {
                "answer": "All high-margin items are currently stocked with sufficient safety buffer.",
                "tamil_summary": "அதிக லாபம் தரும் அனைத்துப் பொருட்களும் போதிய அளவில் இருப்பில் உள்ளன.",
                "data": []
            }

        lines = ["**High Profit Items Running Low on Stock (Prioritize for Restock):**"]
        for it in items[:6]:
            lines.append(
                f"• **{it['name']}**: Margin **{it['margin_pct']}%** (Profit: ₹{it['unit_profit']}/unit) "
                f"| Stock: {it['current_stock']} (Reorder Level: {it['reorder_level']})"
            )

        return {
            "answer": "\n".join(lines),
            "tamil_summary": "அதிக லாபம் தரும் சில பொருட்கள் குறைந்த இருப்பில் உள்ளன, உடனடி மறுஆர்டர் தேவை.",
            "data": items
        }

    @classmethod
    def _handle_product_query(cls, prod_name: str) -> Dict[str, Any]:
        matches = AgentTools.query_stock(prod_name)
        if not matches:
            return {
                "answer": f"Could not find any product matching '{prod_name}' in the catalog.",
                "tamil_summary": f"'{prod_name}' என்ற பொருள் பதிவேட்டில் இல்லை.",
                "data": None
            }

        lines = [f"Found {len(matches)} product(s) matching '{prod_name}':"]
        for m in matches[:4]:
            t = f" ({m['tamil_name']})" if m.get("tamil_name") else ""
            lines.append(
                f"• **{m['name']}{t}**: Current Stock: **{m['current_stock']} {m['unit']}** | "
                f"Selling Price: ₹{m['selling_price']:,.2f} | MRP: ₹{m.get('mrp', m['selling_price']):,.2f} | "
                f"Reorder Level: {m['reorder_level']}"
            )

        return {
            "answer": "\n".join(lines),
            "tamil_summary": f"இருப்பு விவரம்: {matches[0]['name']} - {matches[0]['current_stock']} {matches[0]['unit']}.",
            "data": matches
        }

    @staticmethod
    def _extract_product_name(q: str) -> Optional[str]:
        """Extracts common Indian retail product keyword from query text."""
        keywords = [
            "shampoo", "rice", "atta", "oil", "dal", "sugar", "salt", "tea", "coffee",
            "soap", "detergent", "toothpaste", "biscuit", "milk", "butter", "notebook",
            "pen", "battery", "harpic", "surf", "vim", "aavin", "aashirvaad", "ponni",
            "hamam", "horlicks", "boost"
        ]
        for kw in keywords:
            if kw in q:
                return kw
        return None
