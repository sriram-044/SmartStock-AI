import os
import re
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

from backend.ai.tools import AgentTools
from backend.ai.chat_assistant import NaturalLanguageAssistant
from backend.ai.conversation_memory import ConversationMemoryManager
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
1. Ground all numbers strictly in the tool outputs. Never invent or hallucinate product counts, stock levels, or prices.
2. Structure your English response with clear bullet points, bold key metrics, and Indian currency format (e.g. ₹1,250 or ₹1.5 Lakhs).
3. At the end of your answer, ALWAYS include a concise, natural Tamil explanation labeled **தமிழ் விளக்கம்:** summarizing the key insight for Tamil-speaking shopkeepers.
4. Maintain context across conversation turns: if the user asks a follow-up question (e.g., 'which of those has the highest profit margin?' or 'which supplier is best for the first one?'), use the previous conversation history and call relevant tools to answer.
"""

class LLMEngine:
    """
    Unified LLM Router, Agentic Tool Calling, Multi-Turn Memory & Resilient Fallback Engine.
    Supports:
      - Google Gemini (REST API with Native Function Calling)
      - Groq Cloud (REST API with OpenAI-standard Tool Calling)
      - Ollama (Local offline LLM with Tool Calling / Context Injection)
      - Built-in Deterministic AI Assistant (Zero-dependency local fallback)
    """

    @classmethod
    def get_active_provider(cls) -> Dict[str, Any]:
        provider = os.environ.get("LLM_PROVIDER", LLM_PROVIDER or "auto").lower()

        gemini_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
        groq_key = os.environ.get("GROQ_API_KEY", GROQ_API_KEY)
        gemini_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
        groq_model = os.environ.get("GROQ_MODEL", GROQ_MODEL)
        ollama_model = os.environ.get("OLLAMA_MODEL", OLLAMA_MODEL)

        if provider == "gemini" or (provider == "auto" and gemini_key):
            return {
                "provider": "gemini",
                "name": "Google Gemini (Cloud AI)",
                "model": gemini_model,
                "is_configured": bool(gemini_key),
                "is_free": True,
                "type": "cloud"
            }
        elif provider == "groq" or (provider == "auto" and groq_key):
            return {
                "provider": "groq",
                "name": "Groq Cloud (Llama 3.3)",
                "model": groq_model,
                "is_configured": bool(groq_key),
                "is_free": True,
                "type": "cloud"
            }
        elif provider == "ollama":
            return {
                "provider": "ollama",
                "name": "Ollama (Local Offline LLM)",
                "model": ollama_model,
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
    def execute_tool(
        cls,
        tool_name: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
        return_meta: bool = False
    ) -> Any:
        """
        Safely executes a registered tool function, recording execution timing and audit log.
        If return_meta=True, returns (result, duration_ms, error_str). Otherwise returns result.
        """
        t0 = time.time()
        if tool_name not in TOOLS_REGISTRY:
            err = f"Tool '{tool_name}' not found in registry."
            duration = int((time.time() - t0) * 1000)
            ConversationMemoryManager.record_tool_execution(
                session_id=session_id,
                tool_name=tool_name,
                tool_args=args,
                execution_status="FAILED",
                sanitized_result_summary=err,
                execution_time_ms=duration,
                error_details=err
            )
            return ({"error": err}, duration, err) if return_meta else {"error": err}

        func = TOOLS_REGISTRY[tool_name]["func"]
        try:
            res = func(**args)
            duration = int((time.time() - t0) * 1000)
            summary = f"Returned {len(res)} items" if isinstance(res, list) else f"Executed {tool_name}"
            ConversationMemoryManager.record_tool_execution(
                session_id=session_id,
                tool_name=tool_name,
                tool_args=args,
                execution_status="SUCCESS",
                sanitized_result_summary=summary,
                execution_time_ms=duration
            )
            return (res, duration, None) if return_meta else res
        except TypeError:
            try:
                res = func()
                duration = int((time.time() - t0) * 1000)
                ConversationMemoryManager.record_tool_execution(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_args=args,
                    execution_status="SUCCESS",
                    sanitized_result_summary=f"Executed {tool_name} (no args)",
                    execution_time_ms=duration
                )
                return (res, duration, None) if return_meta else res
            except Exception as e:
                duration = int((time.time() - t0) * 1000)
                err = str(e)
                ConversationMemoryManager.record_tool_execution(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_args=args,
                    execution_status="FAILED",
                    sanitized_result_summary=err,
                    execution_time_ms=duration,
                    error_details=err
                )
                return ({"error": err}, duration, err) if return_meta else {"error": err}
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            err = str(e)
            ConversationMemoryManager.record_tool_execution(
                session_id=session_id,
                tool_name=tool_name,
                tool_args=args,
                execution_status="FAILED",
                sanitized_result_summary=err,
                execution_time_ms=duration,
                error_details=err
            )
            return ({"error": err}, duration, err) if return_meta else {"error": err}

    @classmethod
    def chat(
        cls,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        max_tool_rounds: int = 3
    ) -> Dict[str, Any]:
        """
        Main multi-turn chat orchestrator with automated provider fallback chain,
        persistent conversation memory, and multi-round tool calling.
        """
        # 1. Initialize or validate session ID
        active_session_id = ConversationMemoryManager.create_or_get_session(
            session_id=session_id,
            user_id=user_id,
            title=query[:50]
        )

        # 2. Retrieve recent conversation history (last 8 messages for context)
        history_messages = ConversationMemoryManager.get_recent_messages(active_session_id, limit=8)

        # 3. Save current user message into memory
        ConversationMemoryManager.save_message(
            session_id=active_session_id,
            role="user",
            content=query
        )

        # 4. Construct Provider Fallback Chain
        primary_info = cls.get_active_provider()
        primary_name = primary_info["provider"]

        gemini_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
        groq_key = os.environ.get("GROQ_API_KEY", GROQ_API_KEY)

        # Build ordered candidate chain
        candidates: List[str] = []
        if primary_name in ["gemini", "groq", "ollama", "built_in"]:
            candidates.append(primary_name)

        for p in ["gemini", "groq", "ollama", "built_in"]:
            if p not in candidates:
                if p == "gemini" and gemini_key:
                    candidates.append(p)
                elif p == "groq" and groq_key:
                    candidates.append(p)
                elif p == "ollama":
                    candidates.append(p)
                elif p == "built_in":
                    candidates.append(p)

        fallback_chain_log: List[str] = []
        final_response: Optional[Dict[str, Any]] = None
        executed_provider: str = "built_in"
        executed_model: str = "rule-based-fast"
        execution_mode: str = "deterministic"

        # 5. Execute Fallback Chain
        for provider_candidate in candidates:
            try:
                if provider_candidate == "gemini":
                    if not gemini_key:
                        fallback_chain_log.append("gemini: unconfigured API key")
                        continue
                    res = cls._chat_gemini(query, history_messages, active_session_id, max_rounds=max_tool_rounds)
                    if res:
                        final_response = res
                        executed_provider = "gemini"
                        executed_model = os.environ.get("GEMINI_MODEL") or GEMINI_MODEL
                        execution_mode = "llm"
                        break
                    else:
                        fallback_chain_log.append("gemini: empty candidate response")

                elif provider_candidate == "groq":
                    if not groq_key:
                        fallback_chain_log.append("groq: unconfigured API key")
                        continue
                    res = cls._chat_groq(query, history_messages, active_session_id, max_rounds=max_tool_rounds)
                    if res:
                        final_response = res
                        executed_provider = "groq"
                        executed_model = os.environ.get("GROQ_MODEL") or GROQ_MODEL
                        execution_mode = "llm"
                        break
                    else:
                        fallback_chain_log.append("groq: empty response")

                elif provider_candidate == "ollama":
                    ollama_url = os.environ.get("OLLAMA_BASE_URL") or OLLAMA_BASE_URL
                    if not ollama_url or ollama_url == "disabled":
                        fallback_chain_log.append("ollama: disabled")
                        continue
                    res = cls._chat_ollama(query, history_messages, active_session_id)
                    if res:
                        final_response = res
                        executed_provider = "ollama"
                        executed_model = os.environ.get("OLLAMA_MODEL") or OLLAMA_MODEL
                        execution_mode = "local_llm"
                        break
                    else:
                        fallback_chain_log.append("ollama: unavailable or offline")

                elif provider_candidate == "built_in":
                    res = cls._chat_deterministic(query, history_messages)
                    final_response = res
                    executed_provider = "built_in"
                    executed_model = "rule-based-fast"
                    execution_mode = "deterministic"
                    break

            except Exception as e:
                err_msg = f"{provider_candidate} error: {str(e)}"
                fallback_chain_log.append(err_msg)
                print(f"[LLMEngine Fallback] {err_msg}")

        # 6. Safety fallback if all attempts failed
        if not final_response:
            final_response = cls._chat_deterministic(query, history_messages)
            executed_provider = "built_in"
            executed_model = "rule-based-fast"
            execution_mode = "deterministic"

        # 7. Extract English answer and Tamil summary
        answer_text, tamil_summary = cls._extract_tamil_summary(final_response.get("answer", ""))

        fallback_occurred = len(fallback_chain_log) > 0 and executed_provider != primary_name

        # 8. Persist Assistant Response in Memory
        tool_used = final_response.get("tool_used")
        tool_result = final_response.get("data")

        ConversationMemoryManager.save_message(
            session_id=active_session_id,
            role="assistant",
            content=answer_text,
            tamil_summary=tamil_summary,
            provider=executed_provider,
            model=executed_model,
            tool_name=tool_used,
            tool_result=tool_result,
            execution_mode=execution_mode
        )

        return {
            "session_id": active_session_id,
            "query": query,
            "answer": answer_text,
            "tamil_summary": tamil_summary,
            "provider": executed_provider,
            "model": executed_model,
            "execution_mode": execution_mode,
            "fallback_occurred": fallback_occurred,
            "fallback_chain_log": fallback_chain_log,
            "tool_used": tool_used,
            "data": tool_result
        }

    # -------------------------------------------------------------------------
    # Google Gemini Implementation
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_gemini(
        cls,
        query: str,
        history: List[Dict[str, Any]],
        session_id: str,
        max_rounds: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Invokes Google Gemini with native Function Calling & multi-turn history."""
        api_key = os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
        model_name = os.environ.get("GEMINI_MODEL") or GEMINI_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        gemini_tools = []
        for name, spec in TOOLS_REGISTRY.items():
            gemini_tools.append({
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"]
            })

        # Build contents with conversation history
        contents: List[Dict[str, Any]] = []
        for h in history:
            r = "user" if h["role"] == "user" else "model"
            contents.append({"role": r, "parts": [{"text": h["content"]}]})

        # Add current user turn
        contents.append({"role": "user", "parts": [{"text": query}]})

        last_tool_name = None
        last_tool_result = None

        for _ in range(max_rounds):
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "tools": [{"function_declarations": gemini_tools}]
            }

            data = cls._http_post_json(url, payload, timeout_seconds=12)
            if not data or "candidates" not in data or not data["candidates"]:
                return None

            candidate = data["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            # Check for functionCall
            tool_call_part = next((p for p in parts if "functionCall" in p), None)
            if not tool_call_part:
                # Direct text response
                text_ans = "".join(p.get("text", "") for p in parts if "text" in p)
                return {
                    "answer": text_ans,
                    "tool_used": last_tool_name,
                    "data": last_tool_result
                }

            # Execute tool call
            fn_call = tool_call_part["functionCall"]
            fn_name = fn_call.get("name")
            fn_args = fn_call.get("args", {})

            tool_result, _, _ = cls.execute_tool(fn_name, fn_args, session_id=session_id, return_meta=True)
            last_tool_name = fn_name
            last_tool_result = tool_result

            # Append model functionCall and user functionResponse
            contents.append({"role": "model", "parts": [tool_call_part]})
            contents.append({
                "role": "user",
                "parts": [{
                    "functionResponse": {
                        "name": fn_name,
                        "response": {"output": tool_result}
                    }
                }]
            })

        # Final turn if max rounds reached
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents
        }
        final_data = cls._http_post_json(url, payload, timeout_seconds=12)
        if final_data and "candidates" in final_data and final_data["candidates"]:
            f_parts = final_data["candidates"][0].get("content", {}).get("parts", [])
            final_text = "".join(p.get("text", "") for p in f_parts if "text" in p)
            return {"answer": final_text, "tool_used": last_tool_name, "data": last_tool_result}

        return None

    # -------------------------------------------------------------------------
    # Groq Implementation (OpenAI-standard Tool Calling)
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_groq(
        cls,
        query: str,
        history: List[Dict[str, Any]],
        session_id: str,
        max_rounds: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Invokes Groq Cloud with OpenAI-standard Tool Calling & multi-turn history."""
        api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
        model_name = os.environ.get("GROQ_MODEL") or GROQ_MODEL
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

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": query})

        headers = {"Authorization": f"Bearer {api_key}"}
        last_tool_name = None
        last_tool_result = None

        for _ in range(max_rounds):
            payload = {
                "model": model_name,
                "messages": messages,
                "tools": groq_tools,
                "tool_choice": "auto",
                "max_tokens": 1000
            }

            data = cls._http_post_json(url, payload, headers=headers, timeout_seconds=12)
            if not data or "choices" not in data or not data["choices"]:
                return None

            msg = data["choices"][0].get("message", {})
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                return {
                    "answer": msg.get("content", ""),
                    "tool_used": last_tool_name,
                    "data": last_tool_result
                }

            messages.append(msg)
            for t_call in tool_calls:
                fn_name = t_call["function"]["name"]
                try:
                    fn_args = json.loads(t_call["function"].get("arguments", "{}"))
                except Exception:
                    fn_args = {}

                tool_res, _, _ = cls.execute_tool(fn_name, fn_args, session_id=session_id, return_meta=True)
                last_tool_name = fn_name
                last_tool_result = tool_res

                messages.append({
                    "role": "tool",
                    "tool_call_id": t_call["id"],
                    "name": fn_name,
                    "content": json.dumps(tool_res, ensure_ascii=False)
                })

        return None

    # -------------------------------------------------------------------------
    # Ollama Implementation (Local Offline)
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_ollama(
        cls,
        query: str,
        history: List[Dict[str, Any]],
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Invokes local Ollama server with tool inspection."""
        base_url = os.environ.get("OLLAMA_BASE_URL") or OLLAMA_BASE_URL
        model_name = os.environ.get("OLLAMA_MODEL") or OLLAMA_MODEL
        url = f"{base_url.rstrip('/')}/api/chat"

        # Pre-inspect with deterministic keyword matching to provide live data
        det_res = NaturalLanguageAssistant.ask(query)
        tool_data_ctx = json.dumps(det_res.get("data", {}), ensure_ascii=False)

        augmented_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"LIVE INVENTORY DATABASE CONTEXT:\n{tool_data_ctx}\n\n"
            f"User Question: {query}"
        )

        messages = []
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": augmented_prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }

        data = cls._http_post_json(url, payload, timeout_seconds=15)
        if data and "message" in data:
            return {
                "answer": data["message"].get("content", ""),
                "tool_used": "local_database_inspection",
                "data": det_res.get("data")
            }
        return None

    # -------------------------------------------------------------------------
    # Built-in Deterministic AI Engine (Zero-dependency fallback)
    # -------------------------------------------------------------------------
    @classmethod
    def _chat_deterministic(
        cls,
        query: str,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Executes deterministic inventory introspection with context resolution."""
        # Check if follow-up refers to previous products
        resolved_query = query
        if history and len(history) >= 2:
            last_bot_msg = history[-1].get("content", "")
            if any(term in query.lower() for term in ["which one", "the first one", "highest profit", "best supplier"]):
                resolved_query = f"{query} (Context: {last_bot_msg[:120]})"

        res = NaturalLanguageAssistant.ask(resolved_query)
        return {
            "answer": res.get("answer", ""),
            "tamil_summary": res.get("tamil_summary", ""),
            "tool_used": "deterministic_rules",
            "data": res.get("data")
        }

    # -------------------------------------------------------------------------
    # Helpers: Tamil Extraction, HTTP Networking & JSON Parsing
    # -------------------------------------------------------------------------
    @classmethod
    def _extract_tamil_summary(cls, text: str) -> Tuple[str, str]:
        """Separates the English content from the Tamil explanation."""
        tamil_markers = ["**தமிழ் விளக்கம்:**", "தமிழ் விளக்கம்:", "Tamil Summary:"]
        for marker in tamil_markers:
            if marker in text:
                parts = text.split(marker, 1)
                english = parts[0].strip()
                tamil = parts[1].strip()
                return english, tamil

        # If text contains Tamil characters directly
        tamil_chars = re.findall(r'[\u0B80-\u0BFF]+', text)
        if len(tamil_chars) > 3:
            return text, " ".join(tamil_chars[:20])

        return text, "இருப்பு விவரங்கள் மற்றும் பரிந்துரைகள் பகுப்பாய்வு செய்யப்பட்டுள்ளன."

    @classmethod
    def _http_post_json(
        cls,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 12
    ) -> Optional[Dict[str, Any]]:
        """Makes an HTTP POST request returning parsed JSON response."""
        req_headers = {
            "Content-Type": "application/json",
            "User-Agent": "StockMind-AI/2.0"
        }
        if headers:
            req_headers.update(headers)

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                if 200 <= response.status < 300:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw_err = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
            print(f"[LLMEngine HTTPError] Status {e.code}: {e.reason} | {raw_err[:120]}")
            raise RuntimeError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            print(f"[LLMEngine URLError] {e.reason}")
            raise RuntimeError(f"Connection failed: {e.reason}")
        except Exception as e:
            print(f"[LLMEngine Network Exception] {e}")
            raise RuntimeError(f"Request failed: {str(e)}")

        return None
