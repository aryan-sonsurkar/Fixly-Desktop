from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class InsightService:
    def __init__(self) -> None:
        self.context = WorkspaceContext()
        self.ai_service = AIService()
        self.ai_repo = AIRepository()

    async def generate_insights(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot", include_heatmap=True)
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        study = ctx.get("study", {})
        pomo = ctx.get("pomodoro", {})
        assignments = ctx.get("assignments", {})
        heatmap = ctx.get("heatmap", {})

        daily_data = "\n".join(
            f"{e['date']}: {e['points']}pts, {e['minutes']}m"
            for e in heatmap.get("entries", [])[-30:]
        ) or "No data"

        prompt_kwargs = {
            "user_name": str(profile.get("name", "Student")),
            "weekly_trend": study.get("weekly_trend_str", ""),
            "weekly_hours": str(study.get("total_hours", 0)),
            "study_days": str(study.get("study_days", 0)),
            "avg_daily_minutes": str(study.get("avg_daily", 0)),
            "missed_study_days": str(max(0, 30 - study.get("study_days", 0))),
            "active_assignments": str(assignments.get("total", 0)),
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "overdue_titles": ", ".join(assignments.get("overdue_titles", [])) or "None",
            "weekly_cycles": str(pomo.get("weekly_cycles", 0)),
            "today_focus": str(pomo.get("today_focus_minutes", 0)),
            "xp": str(profile.get("xp", 0)),
            "streak": str(profile.get("streak", 0)),
            "productivity_score": "50",
            "daily_study_data": daily_data,
            "current_time": now.strftime("%H:%M"),
        }

        conv = await self.ai_repo.create_conversation(user_id, "AI Insights")
        prompt = await PromptManager().build(PromptType.INSIGHTS, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        return {
            "content": result["message"]["content"],
            "generated_at": now.isoformat(),
        }

    async def get_daily_mission(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot", include_planner=True)
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        study = ctx.get("study", {})
        pomo = ctx.get("pomodoro", {})
        email = ctx.get("email", {})
        assignments = ctx.get("assignments", {})
        planner_ctx = ctx.get("planner", {})

        today_session = planner_ctx.get("today_sessions", "No sessions")
        deadlines_text = "\n".join(
            f"- {d['title']} (Due: {d['due']}, Priority: {d['priority']})"
            for d in assignments.get("deadlines", [])[:10]
        ) or "No deadlines."

        prompt_kwargs = {
            "user_name": str(profile.get("name", "Student")),
            "current_time": now.strftime("%H:%M"),
            "timezone": str(ctx.get("timezone", "UTC")),
            "active_assignments": str(assignments.get("total", 0)),
            "deadlines": deadlines_text,
            "today_focus": str(pomo.get("today_focus_minutes", 0)),
            "today_xp": str(today_session.get("today_points", 0)),
            "streak": str(profile.get("streak", 0)),
            "productivity_score": "50",
            "weekly_hours": str(study.get("total_hours", 0)),
            "study_days": str(study.get("study_days", 0)),
            "avg_daily_minutes": str(study.get("avg_daily", 0)),
            "weekly_cycles": str(pomo.get("weekly_cycles", 0)),
            "unread_emails": str(email.get("unread", 0)),
            "pending_reviews": str(email.get("pending_review", 0)),
            "planner_context": today_session,
        }

        conv = await self.ai_repo.create_conversation(user_id, "Daily Mission")
        prompt = await PromptManager().build(PromptType.DAILY_MISSION, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        return {
            "content": result["message"]["content"],
            "generated_at": now.isoformat(),
            "context_summary": {
                "active_assignments": assignments.get("total", 0),
                "today_focus": pomo.get("today_focus_minutes", 0),
                "streak": profile.get("streak", 0),
            },
        }

    async def get_weekly_review(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot", include_heatmap=True)
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        study = ctx.get("study", {})
        pomo = ctx.get("pomodoro", {})
        email = ctx.get("email", {})
        assignments = ctx.get("assignments", {})

        week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        period = f"{week_start} to {now.strftime('%Y-%m-%d')}"
        subjects_list = ctx.get("subjects", [])
        subjects_studied = "\n".join(f"- {s.get('name', '')}" for s in subjects_list) or "No subjects"

        trend = study.get("weekly_trend", [])
        peak_day = max(trend, key=lambda d: d.get("points", 0)) if trend else {}
        lowest_day = min(trend, key=lambda d: d.get("points", 0)) if trend else {}

        prompt_kwargs = {
            "user_name": str(profile.get("name", "Student")),
            "review_period": period,
            "weekly_hours": str(study.get("total_hours", 0)),
            "study_days": str(study.get("study_days", 0)),
            "avg_daily_minutes": str(study.get("avg_daily", 0)),
            "weekly_xp": str(sum(d.get("points", 0) for d in trend)),
            "weekly_cycles": str(pomo.get("weekly_cycles", 0)),
            "weekly_focus_minutes": str(pomo.get("today_focus_minutes", 0)),
            "productivity_score": "50",
            "streak": str(profile.get("streak", 0)),
            "completed_assignments": str(len(assignments.get("deadlines", [])) - assignments.get("overdue_count", 0)),
            "active_assignments": str(assignments.get("total", 0)),
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "overdue_titles": ", ".join(assignments.get("overdue_titles", [])) or "None",
            "weekly_trend": study.get("weekly_trend_str", ""),
            "peak_day": str(peak_day.get("date", "N/A")),
            "lowest_day": str(lowest_day.get("date", "N/A")),
            "subjects_studied": subjects_studied,
            "new_emails": str(email.get("unread", 0)),
            "pending_reviews": str(email.get("pending_review", 0)),
        }

        conv = await self.ai_repo.create_conversation(user_id, "Weekly Review")
        prompt = await PromptManager().build(PromptType.WEEKLY_REVIEW, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        return {
            "content": result["message"]["content"],
            "generated_at": now.isoformat(),
        }

