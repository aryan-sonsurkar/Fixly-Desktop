from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.subject_repository import SubjectRepository

logger = get_logger(__name__)

BUDGETS = {
    "full": 4000,
    "briefing": 2000,
    "planner": 3000,
    "copilot": 5000,
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
        self.notification_repo = NotificationRepository()

    async def gather(
        self, user_id: str, budget: str = "full",
        include_planner: bool = False,
        include_ai_chats: bool = False,
        include_heatmap: bool = False,
        include_diary: bool = False,
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

        ctx["timezone"] = await self._get_timezone(user_id)
        remaining -= 10

        ctx["notifications"] = await self._get_notifications(user_id)
        remaining -= ctx["notifications"].get("_tokens", 0)

        if remaining > 500:
            ctx["documents"] = await self._get_recent_documents(user_id)
            remaining -= ctx["documents"].get("_tokens", 0)

        if include_planner and remaining > 400:
            ctx["planner"] = await self._get_planner_context(user_id)
            remaining -= ctx["planner"].get("_tokens", 0)

        if include_ai_chats and remaining > 300:
            ctx["ai_chats"] = await self._get_ai_chats(user_id)
            remaining -= 50

        if include_heatmap and remaining > 300:
            ctx["heatmap"] = await self._get_heatmap(user_id)
            remaining -= ctx["heatmap"].get("_tokens", 0)

        if include_diary and remaining > 200:
            ctx["diary"] = await self._get_diary(user_id)
            remaining -= ctx["diary"].get("_tokens", 0)

        if remaining > 200:
            ctx["conversations"] = await self._get_recent_conversations(user_id)

        ctx["_budget_used"] = max_tokens - remaining
        ctx["_budget_total"] = max_tokens
        return ctx

    def _get_now(self) -> datetime:
        return datetime.now(timezone.utc)

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
        overdue = []
        urgent = []
        for a in pending:
            entry = {"title": a.get("title", ""), "due": str(a.get("due_date", "") or "")[:10], "priority": a.get("priority", "medium"), "status": a.get("status", "")}  # noqa: E501
            deadlines.append(entry)
            tokens += 30
            if entry["priority"] in ("high", "urgent"):
                urgent.append(entry)
            due_str = entry["due"]
            if due_str and due_str < now.strftime("%Y-%m-%d"):
                overdue.append(entry)
        return {
            "total": total,
            "deadlines": deadlines,
            "overdue_count": len(overdue),
            "overdue_titles": [d["title"] for d in overdue],
            "urgent_deadlines": [d["title"] for d in urgent],
            "_tokens": min(tokens, 1500),
        }

    async def _get_pomodoro_summary(self, user_id: str) -> dict[str, Any]:
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            sessions = await self.pomodoro_repo.get_sessions_range(user_id, week_ago, today)
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
            trend = stats.get("weekly_trend", [])[-7:]
            trend_str = ", ".join(f"{d['date']}: {d['points']}" for d in trend)
            return {
                "total_hours": stats.get("total_study_hours", 0),
                "study_days": stats.get("total_study_days", 0),
                "avg_daily": stats.get("average_daily_study_minutes", 0),
                "weekly_trend": trend,
                "weekly_trend_str": trend_str,
                "_tokens": tokens + len(trend) * 10,
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

    async def _get_notifications(self, user_id: str) -> dict[str, Any]:
        try:
            unread_notifs, _ = await self.notification_repo.list_notifications(
                user_id, unread_only=True, limit=10
            )
            return {
                "unread_count": len(unread_notifs),
                "recent": [
                    {"title": n.get("title", ""), "type": n.get("type", ""), "created_at": str(n.get("created_at", ""))[:10]}  # noqa: E501
                    for n in unread_notifs[:5]
                ],
                "_tokens": 30,
            }
        except Exception as e:
            logger.warning("Failed to get notifications: %s", e)
            return {"unread_count": 0, "recent": [], "_tokens": 10}

    async def _get_timezone(self, user_id: str) -> str:
        try:
            profile = await self.profile_repo.get_profile(user_id)
            tz = (profile or {}).get("timezone")
            if tz:
                return str(tz)
        except Exception:
            pass
        return "UTC"

    async def _get_planner_context(self, user_id: str) -> dict[str, Any]:
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            day_data = await self.study_repo.get_day(user_id, today)
            sessions = await self.study_repo.get_sessions_for_date(user_id, today)
            session_lines = []
            for s in sessions:
                st = s.get("start_time", "") or ""
                et = s.get("end_time", "") or ""
                dur = s.get("duration_minutes", 0)
                act = s.get("activity_type", "study")
                subj = s.get("subject_name", "")
                session_lines.append(f"{st}-{et} | {dur}m | {act} | {subj}")
            return {
                "today_sessions": "\n".join(session_lines) if session_lines else "No sessions today.",
                "today_points": (day_data or {}).get("study_points", 0),
                "_tokens": len(session_lines) * 15 + 20,
            }
        except Exception as e:
            logger.warning("Failed to get planner context: %s", e)
            return {"today_sessions": "Unavailable.", "today_points": 0, "_tokens": 10}

    async def _get_ai_chats(self, user_id: str) -> list[dict[str, Any]]:
        try:
            convs = await self.ai_repo.list_conversations(user_id)
            return [
                {"title": c.get("title", ""), "message_count": c.get("message_count", 0), "updated_at": str(c.get("updated_at", ""))[:10]}  # noqa: E501
                for c in convs[:10]
            ]
        except Exception as e:
            logger.warning("Failed to get AI chats: %s", e)
            return []

    async def _get_heatmap(self, user_id: str) -> dict[str, Any]:
        try:
            year = datetime.now(timezone.utc).year
            days = await self.study_repo.get_calendar_days(user_id, year)
            entries = [{"date": d.get("date", ""), "points": d.get("study_points", 0), "minutes": d.get("total_study_minutes", 0)} for d in days[-90:]]  # noqa: E501
            return {"entries": entries, "count": len(entries), "_tokens": len(entries) * 3 + 20}
        except Exception as e:
            logger.warning("Failed to get heatmap: %s", e)
            return {"entries": [], "count": 0, "_tokens": 10}

    async def _get_diary(self, user_id: str) -> dict[str, Any]:
        try:
            now = datetime.now(timezone.utc)
            note = await self.study_repo.get_note(user_id, now.strftime("%Y-%m-%d"))
            return {
                "today_note": (note or {}).get("content", "No entry for today."),
                "date": now.strftime("%Y-%m-%d"),
                "_tokens": 40,
            }
        except Exception as e:
            logger.warning("Failed to get diary: %s", e)
            return {"today_note": "No entry.", "date": "", "_tokens": 10}

    async def _get_recent_documents(self, user_id: str) -> dict[str, Any]:
        try:
            docs = await self.document_repo.get_recent_documents(user_id, limit=5)
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
