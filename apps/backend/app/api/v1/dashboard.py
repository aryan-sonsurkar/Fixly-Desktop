from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.services.assignment_service import AssignmentService
from app.services.profile_service import ProfileService
from app.services.subject_service import SubjectService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    profile_service = ProfileService()
    assignment_service = AssignmentService()
    subject_service = SubjectService()

    profile = await profile_service.get_profile(current_user["id"])
    settings = await profile_service.get_settings(current_user["id"])
    stats = await assignment_service.get_stats(current_user["id"])
    subjects = await subject_service.list_subjects(current_user["id"])
    recent = await assignment_service.list_assignments(
        current_user["id"],
        {
            "page": 1,
            "page_size": 5,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "is_archived": False,
        },
    )

    return {
        "profile": {
            "display_name": profile.get("display_name") or profile.get("full_name") or "Student",
            "avatar_url": profile.get("avatar_url"),
            "xp": profile.get("xp", 0),
            "streak": profile.get("streak", 0),
            "education_type": profile.get("education_type"),
            "education_year": profile.get("education_year"),
        },
        "settings": {
            "daily_goal_hours": settings.get("daily_goal_hours", 0),
            "theme": settings.get("theme", "dark"),
            "daily_briefing": settings.get("daily_briefing", True),
        },
        "stats": stats,
        "recent_assignments": recent.get("data", []),
        "subjects": [
            {"id": s["id"], "name": s["name"], "color": s.get("color"), "icon": s.get("icon")}
            for s in subjects
        ],
    }
