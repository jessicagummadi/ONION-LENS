from fastapi import APIRouter
from backend.app.config import AI_MODEL_STATUS, AI_MODEL_BACKEND

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health_check():
    return {
        "status": "online",
        "app": "Onion Lens",
        "version": "2.0.0",
        "ai_model_status": AI_MODEL_STATUS,
        "ai_model_backend": AI_MODEL_BACKEND,
        "features": {
            "individual_onion_counting": True,
            "opencv_watershed_segmentation": True,
            "deterministic_grading": True,
            "agmark_compliance": True
        }
    }
