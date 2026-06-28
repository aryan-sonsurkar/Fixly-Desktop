from app.api.v1.ai import router as ai_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.profile import router as profile_router
from app.api.v1.subjects import router as subjects_router
from app.api.v1.uploads import router as uploads_router

routers = [
    ai_router,
    assignments_router,
    auth_router,
    dashboard_router,
    profile_router,
    subjects_router,
    uploads_router,
]
