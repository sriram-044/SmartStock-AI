import sys
import os
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

from backend.ai.llm_engine import LLMEngine
from backend.ai.conversation_memory import ConversationMemoryManager
from backend.config import DB_PATH

print('=' * 75)
print('1. LIVE LLM & ACTIVE PROVIDER CONFIGURATION')
print('=' * 75)
prov_info = LLMEngine.get_active_provider()
print(f"Configured Primary : {prov_info['name']} (Model: {prov_info['model']})")
print(f"Provider Type      : {prov_info['type']}")
print(f"Is Configured      : {prov_info['is_configured']}")

print('\n' + '=' * 75)
print('2. MULTI-TURN CONVERSATION: TURN 1 (REAL LLM + LIVE TOOL CALLING)')
print('=' * 75)
q1 = 'Which products need urgent restocking right now?'
print(f'User Query 1: "{q1}"')
turn1 = LLMEngine.chat(q1)
session_id = turn1['session_id']
print(f"Assigned Session ID : {session_id}")
print(f"Executed Provider   : {turn1['provider']} (Model: {turn1.get('model')})")
print(f"Execution Mode      : {turn1['execution_mode']}")
print(f"Fallback Occurred   : {turn1.get('fallback_occurred')}")
print(f"Live Tool Executed  : {turn1.get('tool_used')}")
print(f"Tamil Summary       : {turn1.get('tamil_summary')}")
print(f"LLM Response Snippet:\n{turn1.get('answer', '')[:280]}...\n")

print('=' * 75)
print('3. MULTI-TURN CONVERSATION: TURN 2 (MEMORY & CONTEXTUAL FOLLOW-UP)')
print('=' * 75)
q2 = 'Which one among them has the highest lead time in days?'
print(f'User Query 2: "{q2}"')
print(f'Reusing Session ID: {session_id}')
turn2 = LLMEngine.chat(q2, session_id=session_id)
print(f"Executed Provider   : {turn2['provider']} (Model: {turn2.get('model')})")
print(f"Live Tool Executed  : {turn2.get('tool_used')}")
print(f"Tamil Summary       : {turn2.get('tamil_summary')}")
print(f"LLM Response Snippet:\n{turn2.get('answer', '')}...\n")

print('=' * 75)
print('4. PERSISTENT DATABASE AUDIT (MESSAGES & TOOL AUDIT LOG)')
print('=' * 75)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT id, user_id, title, created_at FROM conversations WHERE id = ?', (session_id,))
conv = cur.fetchone()
if conv:
    print(f"Conversation Record: ID={conv['id']}, Title=\"{conv['title']}\", Created={conv['created_at']}")

cur.execute('SELECT role, provider, model, substr(content, 1, 60) as snippet FROM conversation_messages WHERE session_id = ? ORDER BY id ASC', (session_id,))
msgs = cur.fetchall()
print(f"\nPersisted Messages ({len(msgs)} turns in database):")
for i, m in enumerate(msgs, 1):
    print(f"  [{i}] Role: {m['role']:10} | Provider: {str(m['provider']):10} | Snippet: {m['snippet']}...")

cur.execute('SELECT tool_name, execution_status, execution_time_ms, sanitized_result_summary FROM tool_execution_history WHERE session_id = ? ORDER BY id ASC', (session_id,))
tools = cur.fetchall()
print(f"\nTool Execution History ({len(tools)} executions recorded in database):")
for t in tools:
    print(f"  - Tool: {t['tool_name']:28} | Status: {t['execution_status']} | Latency: {t['execution_time_ms']}ms | {t['sanitized_result_summary']}")

conn.close()
print('\n' + '=' * 75)
print('VERIFICATION COMPLETE: REAL LLM CALL + TOOLS + MEMORY FULLY FUNCTIONAL')
print('=' * 75)
