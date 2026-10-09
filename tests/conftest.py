import os
import shutil
import tempfile
from pathlib import Path
import pytest

@pytest.fixture(scope="session", autouse=True)
def isolated_test_database():
    """
    Creates an isolated copy of the database for the test session.
    Guarantees the main inventory_ai.db is never mutated by test runs.
    """
    base_dir = Path(__file__).resolve().parent.parent
    main_db = base_dir / "inventory_ai.db"
    
    # Create temporary directory for the isolated test database
    temp_dir = tempfile.mkdtemp(prefix="stockmind_test_")
    test_db_path = Path(temp_dir) / "test_inventory.db"
    
    if main_db.exists():
        shutil.copyfile(str(main_db), str(test_db_path))
    else:
        # Initialize and seed if main_db is missing
        old_val = os.environ.get("INVENTORY_DB_PATH")
        os.environ["INVENTORY_DB_PATH"] = str(test_db_path)
        from backend.database.db import init_db
        from data.seed_data import seed_database
        init_db(str(test_db_path))
        seed_database(force=True)
        if old_val:
            os.environ["INVENTORY_DB_PATH"] = old_val

    # Set environment variable so all backend services point to the test db
    orig_env = os.environ.get("INVENTORY_DB_PATH")
    os.environ["INVENTORY_DB_PATH"] = str(test_db_path)
    
    yield str(test_db_path)
    
    # Cleanup
    if orig_env is not None:
        os.environ["INVENTORY_DB_PATH"] = orig_env
    else:
        os.environ.pop("INVENTORY_DB_PATH", None)
        
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass
