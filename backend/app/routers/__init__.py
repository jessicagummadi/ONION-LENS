from backend.app.routers.health import router as health_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.analyze import router as analyze_router
from backend.app.routers.inspections import router as inspections_router

__all__ = ["health_router", "auth_router", "analyze_router", "inspections_router"]
