import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database.db import get_db, transaction

class ConversationMemoryManager:
    """
    Database-backed Multi-Turn Conversation Memory Manager.
    Handles session creation, multi-turn context retention, message persistence,
    user isolation, and tool execution audit logging.
    """

    @classmethod
    def create_or_get_session(
        cls,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        title: Optional[str] = None
    ) -> str:
        """
        Validates existing session_id or creates a new one in the database.
        Enforces user ownership if user_id is provided.
        """
        conn = get_db()
        try:
            if session_id:
                cur = conn.execute("SELECT id, user_id FROM conversations WHERE id = ?", (session_id,))
                row = cur.fetchone()
                if row:
                    # If session exists and user_id is provided, check user ownership (allow if user_id matches or session user_id is None)
                    if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
                        # Session belongs to another user; generate new isolated session
                        session_id = None
                    else:
                        return row["id"]

            # Generate new session ID
            new_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            default_title = title or "New Inventory Discussion"

            effective_user_id = None
            if user_id is not None:
                u_cur = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if u_cur.fetchone():
                    effective_user_id = user_id
                else:
                    try:
                        with transaction() as u_tx:
                            u_tx.execute(
                                "INSERT INTO users (id, username, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)",
                                (user_id, f"user_{user_id}_{uuid.uuid4().hex[:4]}", "hash", f"User {user_id}", "manager")
                            )
                        effective_user_id = user_id
                    except Exception:
                        effective_user_id = None

            with transaction() as tx_conn:
                tx_conn.execute(
                    """
                    INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (new_session_id, effective_user_id, default_title)
                )

            return new_session_id
        finally:
            conn.close()

    @classmethod
    def save_message(
        cls,
        session_id: str,
        role: str,
        content: str,
        tamil_summary: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Any] = None,
        execution_mode: str = "llm"
    ) -> int:
        """Persists a message in the conversation session."""
        tool_args_str = json.dumps(tool_args, ensure_ascii=False) if tool_args else None
        tool_result_str = json.dumps(tool_result, ensure_ascii=False) if tool_result else None

        with transaction() as conn:
            cur = conn.execute(
                """
                INSERT INTO conversation_messages (
                    session_id, role, content, tamil_summary, provider, model,
                    tool_name, tool_args_json, tool_result_json, execution_mode, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    session_id, role, content, tamil_summary, provider, model,
                    tool_name, tool_args_str, tool_result_str, execution_mode
                )
            )
            msg_id = cur.lastrowid

            # Update conversation title from first user message if default
            if role == "user":
                conn.execute(
                    """
                    UPDATE conversations
                    SET title = CASE WHEN title = 'New Inventory Discussion' THEN ? ELSE title END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (content[:60], session_id)
                )

            return msg_id

    @classmethod
    def get_recent_messages(
        cls,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the last N messages for a session to construct LLM conversation context.
        Returns messages ordered chronologically (oldest to newest).
        """
        conn = get_db()
        try:
            cur = conn.execute(
                """
                SELECT id, role, content, tamil_summary, provider, model,
                       tool_name, tool_args_json, tool_result_json, execution_mode, created_at
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cur.fetchall()
            messages = []
            for r in reversed(rows):
                msg = {
                    "id": r["id"],
                    "role": r["role"],
                    "content": r["content"],
                    "tamil_summary": r["tamil_summary"],
                    "provider": r["provider"],
                    "model": r["model"],
                    "tool_name": r["tool_name"],
                    "execution_mode": r["execution_mode"],
                    "created_at": r["created_at"]
                }
                if r["tool_args_json"]:
                    try:
                        msg["tool_args"] = json.loads(r["tool_args_json"])
                    except Exception:
                        msg["tool_args"] = r["tool_args_json"]
                if r["tool_result_json"]:
                    try:
                        msg["tool_result"] = json.loads(r["tool_result_json"])
                    except Exception:
                        msg["tool_result"] = r["tool_result_json"]
                messages.append(msg)
            return messages
        finally:
            conn.close()

    @classmethod
    def list_conversations(
        cls,
        user_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lists conversations for a given user with latest message preview."""
        conn = get_db()
        try:
            if user_id is not None:
                cur = conn.execute(
                    """
                    SELECT c.id, c.user_id, c.title, c.created_at, c.updated_at,
                           (SELECT COUNT(*) FROM conversation_messages m WHERE m.session_id = c.id) as message_count,
                           (SELECT content FROM conversation_messages m WHERE m.session_id = c.id ORDER BY id DESC LIMIT 1) as last_message
                    FROM conversations c
                    WHERE c.user_id = ? OR c.user_id IS NULL
                    ORDER BY c.updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
            else:
                cur = conn.execute(
                    """
                    SELECT c.id, c.user_id, c.title, c.created_at, c.updated_at,
                           (SELECT COUNT(*) FROM conversation_messages m WHERE m.session_id = c.id) as message_count,
                           (SELECT content FROM conversation_messages m WHERE m.session_id = c.id ORDER BY id DESC LIMIT 1) as last_message
                    FROM conversations c
                    ORDER BY c.updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @classmethod
    def get_conversation_history(
        cls,
        session_id: str,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieves a full conversation session with all its messages."""
        conn = get_db()
        try:
            cur = conn.execute("SELECT * FROM conversations WHERE id = ?", (session_id,))
            conv = cur.fetchone()
            if not conv:
                return None

            # Enforce user isolation
            if user_id is not None and conv["user_id"] is not None and conv["user_id"] != user_id:
                return None

            messages = cls.get_recent_messages(session_id, limit=50)
            return {
                "session_id": conv["id"],
                "user_id": conv["user_id"],
                "title": conv["title"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "messages": messages
            }
        finally:
            conn.close()

    @classmethod
    def delete_conversation(
        cls,
        session_id: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Deletes a conversation session and all related messages."""
        conn = get_db()
        try:
            cur = conn.execute("SELECT user_id FROM conversations WHERE id = ?", (session_id,))
            row = cur.fetchone()
            if not row:
                return False
            if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
                return False

            with transaction() as tx_conn:
                tx_conn.execute("DELETE FROM conversations WHERE id = ?", (session_id,))
            return True
        finally:
            conn.close()

    @classmethod
    def record_tool_execution(
        cls,
        session_id: Optional[str],
        tool_name: str,
        tool_args: Dict[str, Any],
        execution_status: str,
        sanitized_result_summary: str,
        execution_time_ms: int = 0,
        error_details: Optional[str] = None
    ) -> None:
        """Records an immutable audit trace of a tool execution in the database."""
        args_str = json.dumps(tool_args, ensure_ascii=False) if tool_args else None
        try:
            with transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO tool_execution_history (
                        session_id, tool_name, tool_args_json, execution_status,
                        sanitized_result_summary, execution_time_ms, error_details, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        session_id, tool_name, args_str, execution_status,
                        sanitized_result_summary, execution_time_ms, error_details
                    )
                )
        except Exception as e:
            print(f"[ConversationMemoryManager] Error recording tool execution trace: {e}")
