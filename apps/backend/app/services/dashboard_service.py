from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.subject_repository import SubjectRepository
from app.services.planner_service import PlannerService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class DashboardService:
    def __init__(self) -> None:
        self.profile_repo = ProfileRepository()
        self.assignment_repo = AssignmentRepository()
        self.subject_repo = SubjectRepository()
        self.email_repo = EmailRepository()
        self.document_repo = DocumentRepository()
        self.pomodoro_repo = PomodoroRepository()
        self.study_repo = StudyRepository()
        self.notification_repo = NotificationRepository()
        self.planner = PlannerService()
        self.context = WorkspaceContext()

    async def get_dashboard(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="briefing")
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")

        profile = ctx.get("profile", {})
        assignments_data = ctx.get("assignments", {})
        pomodoro_data = ctx.get("pomodoro", {})
        study_data = ctx.get("study", {})
        email_data = ctx.get("email", {})

        pending = [d for d in assignments_data.get("deadlines", []) if d.get("status") in ("pending", "in_progress")]
        urgent = [d for d in pending if d.get("priority") in ("high", "urgent")]
        week_from_now = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        upcoming = [d for d in pending if d.get("due", "") <= week_from_now]

        productivity_score = self._calc_productivity(study_data)
        today_session = await self.study_repo.get_day(user_id, today)
        today_xp = (today_session or {}).get("study_points", 0)

        try:
            recent_docs = await self.document_repo.get_recent_documents(user_id, limit=5)
        except Exception:
            recent_docs = []

        try:
            unread_notifs, _ = await self.notification_repo.list_notifications(user_id, unread_only=True, limit=10)
            unread_notif_count = len(unread_notifs)
        except Exception:
            unread_notif_count = 0

        overdue = [a for a in assignments_data.get("deadlines", []) if a.get("status") == "overdue"]
        due_today_count = sum(1 for a in assignments_data.get("deadlines", [])
                              if a.get("due", "") == today)
        due_this_week_count = sum(1 for a in assignments_data.get("deadlines", [])
                                  if a.get("due", "") <= week_from_now)

        return {
            "profile": {
                "display_name": profile.get("name", "Student"),
                "avatar_url": profile.get("avatar_url"),
                "xp": profile.get("xp", 0),
                "streak": profile.get("streak", 0),
                "education_type": profile.get("education_type"),
                "education_year": profile.get("education_year"),
            },
            "today": {
                "focus_minutes": pomodoro_data.get("today_focus_minutes", 0),
                "xp_earned": today_xp,
                "date": today,
            },
            "assignments": {
                "total": assignments_data.get("total", 0),
                "pending": len(pending),
                "urgent": len(urgent),
                "upcoming_deadlines": upcoming[:5],
            },
            "stats": {
                "total": assignments_data.get("total", 0),
                "completed": assignments_data.get("completed", 0),
                "pending": len(pending),
                "in_progress": assignments_data.get("in_progress", 0),
                "overdue": len(overdue),
                "due_today": due_today_count,
                "due_this_week": due_this_week_count,
                "completion_percentage": productivity_score,
            },
            "recent_assignments": upcoming[:5],
            "email": {
                "unread": email_data.get("unread", 0),
                "pending_review": email_data.get("pending_review", 0),
            },
            "study": {
                "total_hours": study_data.get("total_hours", 0),
                "study_days": study_data.get("study_days", 0),
                "avg_daily_minutes": study_data.get("avg_daily", 0),
                "weekly_trend": study_data.get("weekly_trend", [])[-7:],
            },
            "pomodoro": {
                "weekly_cycles": pomodoro_data.get("weekly_cycles", 0),
            },
            "documents": {
                "recent": [{"id": d.get("id"), "name": d.get("original_name", "Untitled"), "type": d.get("doc_type", "")} for d in recent_docs],  # noqa: E501
            },
            "subjects": [],
            "settings": {},
            "productivity_score": productivity_score,
            "unread_notifications": unread_notif_count,
            "generated_at": now.isoformat(),
        }

    async def get_daily_briefing(self, user_id: str) -> dict[str, Any]:
        dashboard = await self.get_dashboard(user_id)
        plan = await self.planner.generate_daily_plan(user_id)
        return {
            "dashboard": dashboard,
            "plan": plan,
        }

    def _calc_productivity(self, study_data: dict[str, Any]) -> int:
        score = 50
        if study_data.get("study_days", 0) > 0:
            score += 10
        if study_data.get("total_hours", 0) >= 5:
            score += 10
        if study_data.get("avg_daily", 0) >= 60:
            score += 10
        if study_data.get("total_hours", 0) >= 20:
            score += 10
        weekly = study_data.get("weekly_trend", [])
        if len(weekly) >= 5 and all(w.get("points", 0) > 0 for w in weekly[-5:]):
            score += 10
        return min(score, 100)
