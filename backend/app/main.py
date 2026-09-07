import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import STATIC_DIR, UPLOADS_DIR, ROOT_DIR, HOST, PORT
from backend.app.database import init_db
from backend.app.routers import health_router, auth_router, analyze_router, inspections_router

# Initialize database schema
init_db()

app = FastAPI(
    title="Onion Lens - AI-Powered Smart Onion Quality Assessment",
    description="Real computer vision inference pipeline for individual onion counting, defect detection, and AGMARK grading.",
    version="2.0.0"
)

# CORS middleware for cross-origin mobile and web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(inspections_router)

# Mount uploads static folder
if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Mount frontend static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Root endpoint: serves the Onion Lens Single-Page Application
@app.get("/")
@app.get("/index.html")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_file), media_type="text/html")

# Direct APK download route for Android mobile testing
@app.get("/onion-lens.apk")
@app.get("/static/onion-lens.apk")
async def download_apk():
    apk_paths = [
        ROOT_DIR / "onion-lens.apk",
        STATIC_DIR / "onion-lens.apk"
    ]
    for p in apk_paths:
        if p.exists():
            return FileResponse(
                str(p),
                media_type="application/vnd.android.package-archive",
                filename="onion-lens.apk"
            )
    raise HTTPException(status_code=404, detail="APK build not found on server")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("[ONION LENS] FastAPI Production Server Initializing...")
    print(f"Server Host: http://{HOST}:{PORT}")
    print(f"Local Browser: http://127.0.0.1:{PORT}")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT)
