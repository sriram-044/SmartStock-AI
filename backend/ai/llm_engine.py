import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from backend.ai.tools import AgentTools
from backend.ai.chat_assistant import NaturalLanguageAssistant
from backend.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)

# -----------------------------------------------------------------------------
# Tool Definitions Schema (OpenAI / Groq / Ollama / Gemini compatible)
# -----------------------------------------------------------------------------
TOOLS_REGISTRY = {
    "query_stock": {
        "func": AgentTools.query_stock,
        "description": "Searches inventory stock levels, prices, barcodes, and suppliers for products by English name, Tamil name, or barcode.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_query": {
                    "type": "string",
                    "description": "The product name (e.g. 'Ponni rice', 'Aashirvaad Atta', 'shampoo') or barcode to search."
                }
            },
            "required": ["product_query"]
        }
    },
    "get_critical_restock_list": {
        "func": AgentTools.get_critical_restock_list,
        "description": "Returns products that have run out or are below reorder level and need urgent restocking.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_dead_stock_summary": {
        "func": AgentTools.get_dead_stock_summary,
        "description": "Calculates total blocked working capital tied up in dead stock (no sales in 45+ days) and lists worst affected items.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_expiring_batches": {
        "func": AgentTools.get_expiring_batches,
        "description": "Returns all product batches approaching expiry within the specified number of days (default 30 days).",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Lookahead window in days (e.g. 15, 30, 60)."
                }
            },
            "required": []
        }
    },
    "get_supplier_comparison": {
        "func": AgentTools.get_supplier_comparison,
        "description": "Compares available wholesale suppliers for a product based on price, delivery lead time, and reliability.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_query": {
                    "type": "string",
                    "description": "Name of the product (e.g. 'Rice', 'Toor Dal', 'Coconut Oil')."
                }
            },
            "required": ["product_query"]
        }
    },
    "get_top_selling_products": {
        "func": AgentTools.get_top_selling_products,
        "description": "Retrieves top selling products by units sold and revenue in the past 30 days.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top products to retrieve (default 10)."
                }
            },
            "required": []
        }
    },
    "get_high_profit_low_stock": {
        "func": AgentTools.get_high_profit_low_stock,
        "description": "Finds high profit margin products (margin >= 15%) that have low inventory.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "explain_product_reorder": {
        "func": AgentTools.explain_product_reorder,
        "description": "Provides full mathematical safety stock and reorder point explanation for a specific product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_query": {
                    "type": "string",
                    "description": "Name of the product to analyze."
                }
            },
            "required": ["product_query"]
        }
    }
}

SYSTEM_PROMPT = """You are SmartStock AI, an expert retail inventory copilot for Indian supermarkets and Kirana stores (Tamil Nadu edition).
You have access to live database tools. ALWAYS call tools to inspect live stock, suppliers, expiry, sales, and dead stock before answering inventory questions.

Guidelines:
1. Ground all numbers strictly in the tool outputs. Never invent or hallucinate product counts or prices.
2. Structure your English response with clear bullet points, bold key metrics, and Indian currency format (e.g. ₹1,250 or ₹1.5 Lakhs).
3. At the end of your answer, always include a concise, natural Tamil explanation labeled **தமிழ் விளக்கம்:** summarizing the key insight for Tamil-speaking shopkeepers.
"""

class LLMEngine:
    """
    Unified LLM Router & Agentic Tool Calling Engine.
    Supports:
      - Google Gemini (Free Tier / Gemini 2.5 Flash / 1.5 Flash)
      - Groq Cloud (Free Tier / Llama-3.3 70B / Llama-3.1 8B)
      - Ollama (Local 100% Free / llama3.2 / mistral)
      - Local Engine (Built-in zero-dependency deterministic fallback)
    """

    @classmethod
    def get_active_provider(cls) -> Dict[str, Any]:
        """Detects and returns active LLM provider metadata."""
        provider = (LLM_PROVIDER or "auto").lower()

        if provider == "gemini" or (provider == "auto" and GEMINI_API_KEY):
            return {
                "provider": "gemini",
                "name": "Google Gemini (Cloud AI)",
                "model": GEMINI_MODEL,
                "is_configured": bool(GEMINI_API_KEY),
                "is_free": True,
                "type": "cloud"
            }
        elif provider == "groq" or (provider == "auto" and GROQ_API_KEY):
            return {
                "provider": "groq",
                "name": "Groq Cloud (Llama 3.3)",
                "model": GROQ_MODEL,
                "is_configured": bool(GROQ_API_KEY),
                "is_free": True,
                "type": "cloud"
            }
        elif provider == "ollama":
            return {
                "provider": "ollama",
                "name": "Ollama (Local Offline LLM)",
                "model": OLLAMA_MODEL,
                "is_configured": True,
                "is_free": True,
                "type": "local"
            }
        else:
            return {
                "provider": "built_in",
                "name": "Built-in Deterministic AI Engine",
                "model": "rule-based-fast",
                "is_configured": True,
                "is_free": True,
                "type": "built_in"
            }

    @classmethod
    def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Any:
        """Safely executes a registered tool function."""
        if tool_name not in TOOLS_REGISTRY:
            return {"error": f"Tool '{tool_name}' not found."}
        func = TOOLS_REGISTRY[tool_name]["func"]
        try:
            return func(**args)
        except TypeError:
            # Fallback if args don't match exactly
            try:
                return func()
            except Exception as e:
                return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def chat(cls, query: str) -> Dict[str, Any]:
        """Main chat orchestrator with auto LLM tool dispatch and graceful local fallback."""
        active = cls.get_active_provider()
        provider = active["provider"]

        if provider == "gemini" and GEMINI_API_KEY:
            try:
                res = cls._chat_gemini(query)
                if res:
                    return res
            except Exception as e:
                print(f"[LLMEngine] Gemini call failed: {e}. Falling back to local engine.")

        elif provider == "groq" and GROQ_API_KEY:
            try:
                res = cls._chat_groq(query)
                if res:
                    return res
            except Exception as e:
                print(f"[LLMEngine] Groq call failed: {e}. Falling back to local engine.")

        elif provider == "ollama":
            try:
                res = cls._chat_ollama(query)
                if res:
                    return res
            except Exception as e:
                print(f"[LLMEngine] Ollama call failed: {e}. Falling back to local engine.")

        # Default fallback to deterministic built-in engine
        local_res = NaturalLanguageAssistant.ask(query)
        local_res["provider"] = "built_in"
        local_res["model"] = "Deterministic ML Engine"
        return local_res

    # -------------------------------------------------------------------------
    # Google Gemini Implementation
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_gemini(cls, query: str) -> Optional[Dict[str, Any]]:
        """Invokes Google Gemini with native Function Calling."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        # Build Gemini tool declarations
        gemini_tools = []
        for name, spec in TOOLS_REGISTRY.items():
            gemini_tools.append({
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"]
            })

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": query}]}
            ],
            "tools": [{"function_declarations": gemini_tools}]
        }

        # Step 1: Initial model call
        data = cls._http_post_json(url, payload)
        if not data or "candidates" not in data or not data["candidates"]:
            return None

        first_candidate = data["candidates"][0]
        content = first_candidate.get("content", {})
        parts = content.get("parts", [])

        # Check for function call
        tool_call_part = next((p for p in parts if "functionCall" in p), None)
        if not tool_call_part:
            # Direct text response
            text_ans = "".join(p.get("text", "") for p in parts if "text" in p)
            return cls._format_response(query, text_ans, "gemini", GEMINI_MODEL)

        # Step 2: Execute tool
        fn_call = tool_call_part["functionCall"]
        fn_name = fn_call.get("name")
        fn_args = fn_call.get("args", {})
        tool_result = cls.execute_tool(fn_name, fn_args)

        from backend.config import GEMINI_MODEL as current_gemini_model
        # Step 3: Send tool result back to Gemini for final response
        followup_payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": query}]},
                {"role": "model", "parts": [tool_call_part]},
                {
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": fn_name,
                            "response": {"output": tool_result}
                        }
                    }]
                }
            ]
        }

        followup_data = cls._http_post_json(url, followup_payload)
        if followup_data and "candidates" in followup_data and followup_data["candidates"]:
            f_parts = followup_data["candidates"][0].get("content", {}).get("parts", [])
            final_text = "".join(p.get("text", "") for p in f_parts if "text" in p)
            return cls._format_response(query, final_text, "gemini", current_gemini_model, tool_result, fn_name)

        return None

    # -------------------------------------------------------------------------
    # Groq Implementation (OpenAI-compatible)
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_groq(cls, query: str) -> Optional[Dict[str, Any]]:
        """Invokes Groq Cloud with OpenAI-standard Tool Calling."""
        url = "https://api.groq.com/openai/v1/chat/completions"

        groq_tools = []
        for name, spec in TOOLS_REGISTRY.items():
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec["description"],
                    "parameters": spec["parameters"]
                }
            })

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]

        from backend.config import GROQ_MODEL as current_groq_model
        payload = {
            "model": current_groq_model,
            "messages": messages,
            "tools": groq_tools,
            "tool_choice": "auto",
            "max_tokens": 1000
        }

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = cls._http_post_json(url, payload, headers=headers)
        if not data or "choices" not in data or not data["choices"]:
            return None

        choice = data["choices"][0]
        message = choice.get("message", {})

        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return cls._format_response(query, message.get("content", ""), "groq", current_groq_model)

        # Execute first tool call
        t_call = tool_calls[0]
        fn_name = t_call["function"]["name"]
        try:
            fn_args = json.loads(t_call["function"].get("arguments", "{}"))
        except Exception:
            fn_args = {}

        tool_result = cls.execute_tool(fn_name, fn_args)

        # Send tool response back to Groq
        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": t_call["id"],
            "name": fn_name,
            "content": json.dumps(tool_result, ensure_ascii=False)
        })

        followup_payload = {
            "model": current_groq_model,
            "messages": messages,
            "max_tokens": 1000
        }

        followup_data = cls._http_post_json(url, followup_payload, headers=headers)
        if followup_data and "choices" in followup_data and followup_data["choices"]:
            final_text = followup_data["choices"][0].get("message", {}).get("content", "")
            return cls._format_response(query, final_text, "groq", current_groq_model, tool_result, fn_name)

        return None

    # -------------------------------------------------------------------------
    # Ollama Implementation (Local Offline)
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_ollama(cls, query: str) -> Optional[Dict[str, Any]]:
        """Invokes local Ollama server."""
        url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

        # Check if Ollama tool format or simple context-augmented prompt
        # We perform local intent check or fetch tool context for Ollama
        local_ans = NaturalLanguageAssistant.ask(query)
        tool_data = local_ans.get("data")

        prompt = f"User Question: {query}\n\nLive Database Context:\n{json.dumps(tool_data, ensure_ascii=False) if tool_data else 'No specific filter applied.'}"

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }

        data = cls._http_post_json(url, payload, timeout=30)
        if data and "message" in data:
            content = data["message"].get("content", "")
            return cls._format_response(query, content, "ollama", OLLAMA_MODEL, tool_data)

        return None

    # -------------------------------------------------------------------------
    # HTTP Helper
    # -------------------------------------------------------------------------
    @classmethod
    def _http_post_json(cls, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Optional[Dict[str, Any]]:
        """Lightweight zero-dependency HTTP POST requester using standard library."""
        req_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) SmartStock-AI/1.0"
        }
        if headers:
            req_headers.update(headers)

        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"[LLMEngine HTTP Error {e.code}]: {err_body}")
            return None
        except Exception as e:
            print(f"[LLMEngine Request Exception]: {e}")
            return None

    # -------------------------------------------------------------------------
    # Response Formatter
    # -------------------------------------------------------------------------
    @classmethod
    def _format_response(
        cls,
        query: str,
        full_text: str,
        provider: str,
        model: str,
        data: Optional[Any] = None,
        tool_used: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parses English answer and Tamil summary from LLM response, stripping think tags."""
        # Strip reasoning model <think>...</think> tags if present
        clean_text = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()

        tamil_summary = ""
        english_answer = clean_text

        # Extract Tamil section if present
        if "தமிழ் விளக்கம்:" in clean_text:
            parts = clean_text.split("தமிழ் விளக்கம்:")
            english_answer = parts[0].strip()
            tamil_summary = parts[1].strip()
        elif "தமிழ் சுருக்கம்:" in clean_text:
            parts = clean_text.split("தமிழ் சுருக்கம்:")
            english_answer = parts[0].strip()
            tamil_summary = parts[1].strip()

        return {
            "query": query,
            "answer": english_answer,
            "tamil_summary": tamil_summary,
            "data": data,
            "tool_used": tool_used,
            "provider": provider,
            "model": model
        }
