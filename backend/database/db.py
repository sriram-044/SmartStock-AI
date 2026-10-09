import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from backend.config import DB_PATH

def get_db_path() -> str:
    """Returns the effective database path, prioritizing INVENTORY_DB_PATH env var."""
    return os.environ.get("INVENTORY_DB_PATH", DB_PATH)

def get_db(db_path: Optional[str] = None):
    """Returns a connection configured with row_factory as dict-like Row."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_context(db_path: Optional[str] = None):
    """Context manager for auto-closing DB connection."""
    conn = get_db(db_path)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction(db_path: Optional[str] = None):
    """Context manager for atomic transactions with automatic rollback on error."""
    conn = get_db(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path: Optional[str] = None):
    """Initializes the database using schema.sql if tables do not exist."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    target_path = db_path or get_db_path()
    with transaction(target_path) as conn:
        conn.executescript(schema_sql)
    print(f"[DB] Initialized database successfully at: {target_path}")

if __name__ == "__main__":
    init_db()

