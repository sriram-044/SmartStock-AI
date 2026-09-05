import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is in Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    
    print(f"============================================================")
    print(f"  Starting Inventory Management AI Server")
    print(f"  URL: http://{host}:{port}")
    print(f"============================================================")
    
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)
