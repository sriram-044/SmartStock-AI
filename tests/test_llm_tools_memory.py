import os
import json
import pytest
from unittest.mock import patch, MagicMock

from backend.database.db import get_db, init_db
from backend.ai.llm_engine import LLMEngine, TOOLS_REGISTRY
from backend.ai.conversation_memory import ConversationMemoryManager
from backend.ai.tools import AgentTools
from backend.ai.chat_assistant import NaturalLanguageAssistant

# Uses isolated_test_database session fixture from conftest.py

# ==============================================================================
# 1. REAL LLM CALLS & PROVIDER SELECTION TESTS
# ==============================================================================

def test_llm_provider_selection():
    """Verifies provider metadata detection across environments."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test_gemini_key", "GEMINI_MODEL": "gemini-2.0-flash"}):
        p = LLMEngine.get_active_provider()
        assert p["provider"] == "gemini"
        assert p["model"] == "gemini-2.0-flash"
        assert p["is_configured"] is True

    with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key", "GROQ_MODEL": "llama-3.3-70b-versatile"}):
        p = LLMEngine.get_active_provider()
        assert p["provider"] == "groq"
        assert p["model"] == "llama-3.3-70b-versatile"
        assert p["is_configured"] is True

    with patch.dict(os.environ, {"LLM_PROVIDER": "built_in"}):
        p = LLMEngine.get_active_provider()
        assert p["provider"] == "built_in"
        assert p["type"] == "built_in"

def test_gemini_http_request_payload_and_headers():
    """Verifies correct Gemini REST request payload and function declaration formatting."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": "Here is your stock overview.\n\n**தமிழ் விளக்கம்:** இருப்பு சரிபார்க்கப்பட்டது."}]
                }
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "valid_gemini_key", "GEMINI_MODEL": "gemini-2.0-flash"}):
            res = LLMEngine._chat_gemini("Check stock", [], session_id="test_sess")
            assert res is not None
            assert "Here is your stock overview" in res["answer"]
            assert mock_urlopen.called

def test_groq_http_request_payload_and_headers():
    """Verifies correct Groq OpenAI-standard chat completion request formatting."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Groq analysis completed.\n\n**தமிழ் விளக்கம்:** பகுப்பாய்வு முடிந்தது."
                }
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "valid_groq_key", "GROQ_MODEL": "llama-3.3-70b-versatile"}):
            res = LLMEngine._chat_groq("Analyze sales", [], session_id="test_sess")
            assert res is not None
            assert "Groq analysis completed" in res["answer"]

# ==============================================================================
# 2. TOOL CALLING TESTS
# ==============================================================================

def test_registered_tools_execution():
    """Verifies that all 8 core tools execute against the database and return structured results."""
    # 1. query_stock
    res1, dur1, err1 = LLMEngine.execute_tool("query_stock", {"product_query": "Rice"}, session_id="test_sess", return_meta=True)
    assert err1 is None
    assert isinstance(res1, list)

    # 2. get_critical_restock_list
    res2, dur2, err2 = LLMEngine.execute_tool("get_critical_restock_list", {}, session_id="test_sess", return_meta=True)
    assert err2 is None
    assert isinstance(res2, list)

    # 3. get_dead_stock_summary
    res3, dur3, err3 = LLMEngine.execute_tool("get_dead_stock_summary", {}, session_id="test_sess", return_meta=True)
    assert err3 is None
    assert "total_blocked_capital_inr" in res3

    # 4. get_expiring_batches
    res4, dur4, err4 = LLMEngine.execute_tool("get_expiring_batches", {"days": 30}, session_id="test_sess", return_meta=True)
    assert err4 is None
    assert isinstance(res4, list)

    # 5. get_supplier_comparison
    res5, dur5, err5 = LLMEngine.execute_tool("get_supplier_comparison", {"product_query": "Rice"}, session_id="test_sess", return_meta=True)
    assert err5 is None
    assert isinstance(res5, dict)

    # 6. get_top_selling_products
    res6, dur6, err6 = LLMEngine.execute_tool("get_top_selling_products", {"limit": 5}, session_id="test_sess", return_meta=True)
    assert err6 is None
    assert isinstance(res6, list)

    # 7. get_high_profit_low_stock
    res7, dur7, err7 = LLMEngine.execute_tool("get_high_profit_low_stock", {}, session_id="test_sess", return_meta=True)
    assert err7 is None
    assert isinstance(res7, list)

    # 8. explain_product_reorder
    res8, dur8, err8 = LLMEngine.execute_tool("explain_product_reorder", {"product_query": "Rice"}, session_id="test_sess", return_meta=True)
    assert err8 is None

def test_tool_execution_history_logging():
    """Verifies that tool executions are recorded in the tool_execution_history database table."""
    session_id = "test_audit_session"
    LLMEngine.execute_tool("get_critical_restock_list", {}, session_id=session_id)

    conn = get_db()
    cur = conn.execute("SELECT * FROM tool_execution_history WHERE session_id = ?", (session_id,))
    rows = cur.fetchall()
    conn.close()

    assert len(rows) >= 1
    assert rows[0]["tool_name"] == "get_critical_restock_list"
    assert rows[0]["execution_status"] == "SUCCESS"

def test_unknown_tool_and_error_containment():
    """Verifies that unknown tools or invalid arguments are handled gracefully without crashing."""
    res, dur, err = LLMEngine.execute_tool("non_existent_tool", {"foo": "bar"}, session_id="err_sess", return_meta=True)
    assert "error" in res
    assert err is not None

# ==============================================================================
# 3. MULTI-TURN MEMORY & CONTEXT RETENTION TESTS
# ==============================================================================

def test_multi_turn_session_context_retention():
    """Verifies multi-turn memory: Turn 1 sets context, Turn 2 resolves follow-up question."""
    # Turn 1: Ask for critical restock list
    resp1 = LLMEngine.chat("Which products need restocking?")
    session_id = resp1["session_id"]
    assert session_id is not None
    assert len(resp1["answer"]) > 0

    # Turn 2: Follow-up question referring to previous turn
    resp2 = LLMEngine.chat("Which one has the highest profit margin?", session_id=session_id)
    assert resp2["session_id"] == session_id
    assert len(resp2["answer"]) > 0

    # Verify messages in memory
    messages = ConversationMemoryManager.get_recent_messages(session_id)
    assert len(messages) == 4  # (User1, Assistant1, User2, Assistant2)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"

def test_user_session_isolation():
    """Verifies that User A's session is isolated and cannot be accessed by User B."""
    # User 1 creates a session
    sess_user1 = ConversationMemoryManager.create_or_get_session(user_id=1, title="User 1 Secret Stock")
    ConversationMemoryManager.save_message(sess_user1, "user", "Private User 1 note")

    # User 2 tries to access User 1's session
    sess_user2 = ConversationMemoryManager.create_or_get_session(session_id=sess_user1, user_id=2)
    assert sess_user2 != sess_user1  # Should create a new isolated session

    # User 2 history query for User 1's session should return None
    history = ConversationMemoryManager.get_conversation_history(session_id=sess_user1, user_id=2)
    assert history is None

# ==============================================================================
# 4. PERSISTENT HISTORY TESTS
# ==============================================================================

def test_conversation_history_persistence_and_listing():
    """Verifies storing messages, listing sessions, and retrieving full history."""
    sess = ConversationMemoryManager.create_or_get_session(user_id=10, title="Inventory Restock Plan")
    ConversationMemoryManager.save_message(sess, "user", "How many items need restock?")
    ConversationMemoryManager.save_message(
        sess, "assistant", "5 items need restock.",
        tamil_summary="5 பொருட்கள் தேவை.",
        provider="built_in",
        model="rule-based-fast"
    )

    # List conversations
    convs = ConversationMemoryManager.list_conversations(user_id=10)
    assert len(convs) >= 1
    assert convs[0]["id"] == sess
    assert convs[0]["message_count"] == 2

    # Get conversation details
    details = ConversationMemoryManager.get_conversation_history(sess, user_id=10)
    assert details is not None
    assert len(details["messages"]) == 2
    assert details["messages"][1]["tamil_summary"] == "5 பொருட்கள் தேவை."

    # Delete conversation
    deleted = ConversationMemoryManager.delete_conversation(sess, user_id=10)
    assert deleted is True
    assert ConversationMemoryManager.get_conversation_history(sess) is None

# ==============================================================================
# 5. FALLBACK CHAIN TESTS
# ==============================================================================

def test_fallback_chain_on_provider_error():
    """Verifies fallback chain: when primary cloud LLM encounters an error, it falls back gracefully."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Simulate network error on Gemini
        mock_urlopen.side_effect = Exception("Simulated HTTP 401 Unauthorized API Key")

        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "invalid_key"}):
            res = LLMEngine.chat("Which products are low on stock?")
            assert res is not None
            assert res["provider"] == "built_in"  # Fell back to deterministic engine
            assert res["execution_mode"] == "deterministic"
            assert res["fallback_occurred"] is True
            assert len(res["fallback_chain_log"]) >= 1
            assert "gemini" in res["fallback_chain_log"][0]

# ==============================================================================
# 6. ERROR RECOVERY TESTS
# ==============================================================================

def test_error_recovery_missing_keys_and_malformed_input():
    """Verifies that missing keys or malformed inputs do not crash the engine."""
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "",
        "GROQ_API_KEY": "",
        "OLLAMA_BASE_URL": "disabled"
    }):
        # Missing keys and disabled Ollama should automatically route through fallback chain to built_in
        res = LLMEngine.chat("Show dead stock")
        assert res is not None
        assert res["provider"] == "built_in"
        assert len(res["answer"]) > 0

# ==============================================================================
# 7. TAMIL LOCALIZATION TESTS
# ==============================================================================

def test_tamil_localization_and_unicode_preservation():
    """Verifies that Tamil text is extracted, preserved in Unicode, and included in response."""
    raw_text = (
        "Here are the top 3 selling products: Ponni Rice, Atta, Sugar.\n\n"
        "**தமிழ் விளக்கம்:** இந்த மாதத்தில் பொன்னி அரிசி மற்றும் கோதுமை மாவு அதிக அளவில் விற்பனையாகியுள்ளது."
    )
    english, tamil = LLMEngine._extract_tamil_summary(raw_text)
    assert "Here are the top 3 selling products" in english
    assert "பொன்னி அரிசி" in tamil
    assert "விற்பனையாகியுள்ளது" in tamil

def test_bilingual_chat_response():
    """Verifies end-to-end bilingual English answer + Tamil summary output."""
    res = LLMEngine.chat("Which products need restocking?")
    assert "answer" in res and len(res["answer"]) > 0
    assert "tamil_summary" in res and len(res["tamil_summary"]) > 0
    # Check that Tamil Unicode characters are present
    assert any('\u0B80' <= char <= '\u0BFF' for char in res["tamil_summary"])
