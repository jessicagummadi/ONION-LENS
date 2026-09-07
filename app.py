"""
Onion Lens - AI-Powered Smart Onion Quality Assessment
Production FastAPI Application Entrypoint
"""

import sys
import os

# Ensure current directory is on python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from backend.app.main import app
from backend.app.config import HOST, PORT

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("[ONION LENS] Starting FastAPI Production Server...")
    print(f"Server Host: http://{HOST}:{PORT}")
    print(f"Local Browser: http://127.0.0.1:{PORT}")
    print(f"API Docs (Swagger): http://127.0.0.1:{PORT}/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=False)
