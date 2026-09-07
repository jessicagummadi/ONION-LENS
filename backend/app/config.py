import os
from pathlib import Path

# Base Paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
STATIC_DIR = ROOT_DIR / "static"
UPLOADS_DIR = BACKEND_DIR / "uploads"
MODELS_DIR = BACKEND_DIR / "models"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'inspections.db'}")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Model & AI Pipeline Configuration
CUSTOM_WEIGHTS_FILE = MODELS_DIR / "onion_yolo.onnx"
HAS_CUSTOM_WEIGHTS = CUSTOM_WEIGHTS_FILE.exists()

if HAS_CUSTOM_WEIGHTS:
    AI_MODEL_STATUS = "CUSTOM_WEIGHTS_ACTIVE"
    AI_MODEL_BACKEND = "ONNXRuntime/YOLO"
else:
    # Explicit status as required: expose clear system state
    AI_MODEL_STATUS = "OPENCV_INSTANCE_SEGMENTATION_ACTIVE"
    AI_MODEL_BACKEND = "OpenCV-Watershed-Morphology-Pipeline"

# AGMARK Grading Thresholds
AGMARK_STANDARDS = {
    "grade_a": {
        "max_defective_pct": 10.0,
        "max_sprouting_count": 1,
        "max_mold_count": 0,
        "min_avg_diameter_mm": 45.0,
        "min_quality_score": 85
    },
    "urs": {
        "max_defective_pct": 30.0,
        "min_quality_score": 60
    }
}
