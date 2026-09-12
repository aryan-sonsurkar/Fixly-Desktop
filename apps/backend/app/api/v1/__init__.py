from app.api.v1.academic import router as academic_router
from app.api.v1.ai import router as ai_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.email import router as email_router
from app.api.v1.goals import router as goals_router, skills_router, roadmaps_router
from app.api.v1.health import router as health_router
from app.api.v1.memory import router as memory_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.pomodoro import router as pomodoro_router
from app.api.v1.profile import router as profile_router
from app.api.v1.proactive import router as proactive_router
from app.api.v1.search import router as search_router
from app.api.v1.study import router as study_router
from app.api.v1.subjects import router as subjects_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.workflows import router as workflows_router

routers = [
    academic_router,
    ai_router,
    assignments_router,
    auth_router,
    copilot_router,
    health_router,
    dashboard_router,
    documents_router,
    email_router,
    goals_router,
    skills_router,
    roadmaps_router,
    memory_router,
    notifications_router,
    opportunities_router,
    pomodoro_router,
    profile_router,
    proactive_router,
    search_router,
    study_router,
    subjects_router,
    uploads_router,
    workflows_router,
]
