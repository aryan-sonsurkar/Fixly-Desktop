from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.subject_repository import SubjectRepository

logger = get_logger(__name__)

BUDGETS = {
    "full": 4000,
    "briefing": 2000,
    "planner": 3000,
    "search": 1500,
    "quick": 1000,
}


class WorkspaceContext:
    def __init__(self) -> None:
        self.profile_repo = ProfileRepository()
        self.subject_repo = SubjectRepository()
        self.assignment_repo = AssignmentRepository()
        self.email_repo = EmailRepository()
        self.document_repo = DocumentRepository()
        self.pomodoro_repo = PomodoroRepository()
        self.study_repo = StudyRepository()
        self.ai_repo = AIRepository()

    async def gather(
        self, user_id: str, budget: str = "full",
    ) -> dict[str, Any]:
        max_tokens = BUDGETS.get(budget, 2000)
        ctx: dict[str, Any] = {}
        remaining = max_tokens

        ctx["profile"] = await self._get_profile(user_id)
        remaining -= 50

        ctx["subjects"] = await self._get_subjects(user_id)
        remaining -= len(ctx["subjects"]) * 20

        ctx["assignments"] = await self._get_assignments(user_id)
        remaining -= ctx["assignments"].get("_tokens", 0)

        ctx["pomodoro"] = await self._get_pomodoro_summary(user_id)
        remaining -= 50

        ctx["study"] = await self._get_study_summary(user_id)
        remaining -= ctx["study"].get("_tokens", 0)

        ctx["email"] = await self._get_email_summary(user_id)
        remaining -= ctx["email"].get("_tokens", 0)

        if remaining > 500:
            ctx["documents"] = await self._get_recent_documents(user_id)
            remaining -= ctx["documents"].get("_tokens", 0)

        if remaining > 300:
            ctx["conversations"] = await self._get_recent_conversations(user_id)

        ctx["_budget_used"] = max_tokens - remaining
        ctx["_budget_total"] = max_tokens
        return ctx

    async def _get_profile(self, user_id: str) -> dict[str, Any]:
        profile = await self.profile_repo.get_profile(user_id)
        if not profile:
            return {"name": "Student", "education": "Not set"}
        return {
            "name": profile.get("full_name") or profile.get("display_name", "Student"),
            "education": f"{profile.get('education_type', '')} {profile.get('education_year', '')}",
            "branch": profile.get("branch_stream", ""),
            "college": profile.get("college_name", ""),
            "xp": profile.get("xp", 0),
            "streak": profile.get("streak", 0),
        }

    async def _get_subjects(self, user_id: str) -> list[dict[str, Any]]:
        return await self.subject_repo.list_subjects(user_id)

    async def _get_assignments(self, user_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        pending, total = await self.assignment_repo.list_assignments(
            user_id, page=1, page_size=50,
            filters={"status": "pending,in_progress"},
        )
        tokens = 0
        deadlines = []
        for a in pending:
            entry = {"title": a.get("title", ""), "due": str(a.get("due_date", "") or "")[:10], "priority": a.get("priority", "medium"), "status": a.get("status", "")}
            deadlines.append(entry)
            tokens += 30
        return {"total": total, "deadlines": deadlines, "_tokens": min(tokens, 1500)}

    async def _get_pomodoro_summary(self, user_id: str) -> dict[str, Any]:
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sessions = await self.pomodoro_repo.get_sessions(user_id, days=7)
            total_cycles = sum(s.get("cycles_completed", 0) for s in sessions)
            today_sessions = [s for s in sessions if str(s.get("date", "")) == today]
            today_focus = sum(s.get("total_focus_minutes", 0) for s in today_sessions)
            return {
                "weekly_cycles": total_cycles,
                "today_focus_minutes": today_focus,
                "_tokens": 30,
            }
        except Exception as e:
            logger.warning("Failed to get pomodoro summary: %s", e)
            return {"weekly_cycles": 0, "today_focus_minutes": 0, "_tokens": 10}

    async def _get_study_summary(self, user_id: str) -> dict[str, Any]:
        try:
            stats = await self.study_repo.get_statistics(user_id)
            tokens = 50
            return {
                "total_hours": stats.get("total_study_hours", 0),
                "study_days": stats.get("total_study_days", 0),
                "avg_daily": stats.get("average_daily_study_minutes", 0),
                "weekly_trend": stats.get("weekly_trend", [])[-7:],
                "_tokens": tokens,
            }
        except Exception as e:
            logger.warning("Failed to get study summary: %s", e)
            return {"total_hours": 0, "study_days": 0, "avg_daily": 0, "_tokens": 10}

    async def _get_email_summary(self, user_id: str) -> dict[str, Any]:
        try:
            unread = await self.email_repo.get_unread_count(user_id)
            queue = await self.email_repo.get_review_queue(user_id)
            return {"unread": unread, "pending_review": len(queue), "_tokens": 20}
        except Exception as e:
            logger.warning("Failed to get email summary: %s", e)
            return {"unread": 0, "pending_review": 0, "_tokens": 10}

    async def _get_recent_documents(self, user_id: str) -> dict[str, Any]:
        try:
            docs = await self.document_repo.list_documents(user_id, limit=5)
            names = [d.get("original_name", "Untitled") for d in docs]
            return {"recent": names, "count": len(names), "_tokens": len(names) * 15}
        except Exception as e:
            logger.warning("Failed to get documents: %s", e)
            return {"recent": [], "count": 0, "_tokens": 10}

    async def _get_recent_conversations(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return await self.ai_repo.list_conversations(user_id)
        except Exception as e:
            logger.warning("Failed to get conversations: %s", e)
            return []
