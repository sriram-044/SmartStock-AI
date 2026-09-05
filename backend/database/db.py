import sqlite3
from contextlib import contextmanager
from pathlib import Path
from backend.config import DB_PATH

def get_db():
    """Returns a connection configured with row_factory as dict-like Row."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_context():
    """Context manager for auto-closing DB connection."""
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction():
    """Context manager for atomic transactions with automatic rollback on error."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes the database using schema.sql if tables do not exist."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with transaction() as conn:
        conn.executescript(schema_sql)
    print(f"[DB] Initialized database successfully at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
