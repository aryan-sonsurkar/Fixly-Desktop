from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.subjects import router as subjects_router

routers = [auth_router, profile_router, subjects_router]
