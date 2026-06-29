from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService
from app.services.command_service import CommandService
from app.services.insight_service import InsightService
from app.services.risk_detector_service import RiskDetectorService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class CopilotService:
    def __init__(self) -> None:
        self.context = WorkspaceContext()
        self.ai_service = AIService()
        self.ai_repo = AIRepository()
        self.risk_detector = RiskDetectorService()
        self.insight_service = InsightService()
        self.command_service = CommandService()

    async def get_daily_mission(self, user_id: str) -> dict[str, Any]:
        return await self.insight_service.get_daily_mission(user_id)

    async def get_productivity_coach(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot", include_planner=True)
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        study = ctx.get("study", {})
        pomo = ctx.get("pomodoro", {})
        email = ctx.get("email", {})
        assignments = ctx.get("assignments", {})

        last_session = "Not today"
        if pomo.get("today_focus_minutes", 0) > 0:
            last_session = "Today"

        prompt_kwargs = {
            "user_name": str(profile.get("name", "Student")),
            "current_time": now.strftime("%H:%M"),
            "timezone": str(ctx.get("timezone", "UTC")),
            "active_assignments": str(assignments.get("total", 0)),
            "deadlines": "\n".join(
                f"- {d['title']} (Due: {d['due']})" for d in assignments.get("deadlines", [])[:10]
            ) or "None",
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "today_focus": str(pomo.get("today_focus_minutes", 0)),
            "today_xp": str(ctx.get("planner", {}).get("today_points", 0)),
            "streak": str(profile.get("streak", 0)),
            "weekly_hours": str(study.get("total_hours", 0)),
            "weekly_cycles": str(pomo.get("weekly_cycles", 0)),
            "last_study_session": last_session,
            "pending_reviews": str(email.get("pending_review", 0)),
        }

        conv = await self.ai_repo.create_conversation(user_id, "Productivity Coach")
        prompt = await PromptManager().build(PromptType.PRODUCTIVITY_COACH, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        return {
            "content": result["message"]["content"],
            "generated_at": now.isoformat(),
        }

    async def reschedule(self, user_id: str, message: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot", include_planner=True)
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        assignments = ctx.get("assignments", {})
        planner = ctx.get("planner", {})

        planner_text = planner.get("today_sessions", "No sessions")

        deadlines_text = "\n".join(
            f"- {d['title']} (Due: {d['due']})" for d in assignments.get("deadlines", [])[:10]
        ) or "None"

        prompt_kwargs = {
            "user_message": message,
            "user_name": str(profile.get("name", "Student")),
            "current_time": now.strftime("%H:%M"),
            "timezone": str(ctx.get("timezone", "UTC")),
            "active_assignments": str(assignments.get("total", 0)),
            "deadlines": deadlines_text,
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "planner_context": planner_text,
        }

        conv = await self.ai_repo.create_conversation(user_id, f"Reschedule: {message[:50]}")
        prompt = await PromptManager().build(PromptType.RESCHEDULER, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        return {
            "content": result["message"]["content"],
            "generated_at": now.isoformat(),
        }

    async def assess_risk(self, user_id: str) -> dict[str, Any]:
        return await self.risk_detector.assess(user_id)

    async def get_weekly_review(self, user_id: str) -> dict[str, Any]:
        return await self.insight_service.get_weekly_review(user_id)

    async def get_insights(self, user_id: str) -> dict[str, Any]:
        return await self.insight_service.generate_insights(user_id)

    async def interpret_command(self, user_id: str, command: str) -> dict[str, Any]:
        return await self.command_service.interpret(user_id, command)

    async def chat(self, user_id: str, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        if not conversation_id:
            conv = await self.ai_repo.create_conversation(user_id, "Copilot Chat")
            conversation_id = conv["id"]

        ctx = await self.context.gather(user_id, budget="copilot")
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        assignments = ctx.get("assignments", {})
        pomo = ctx.get("pomodoro", {})

        context_prompt = (
            f"[Academic Context for {profile.get('name', 'Student')}]\n"
            f"- Active assignments: {assignments.get('total', 0)} (Overdue: {assignments.get('overdue_count', 0)})\n"
            f"- Today's focus: {pomo.get('today_focus_minutes', 0)} min\n"
            f"- Streak: {profile.get('streak', 0)} days\n"
            f"- XP: {profile.get('xp', 0)}\n"
            f"- Timezone: {ctx.get('timezone', 'UTC')}\n"
            f"- Current time: {now.strftime('%H:%M')}\n\n"
        )

        full_message = context_prompt + message
        result = await self.ai_service.chat(user_id, full_message, conversation_id, stream=False)

        return {
            "content": result["message"]["content"],
            "conversation_id": conversation_id,
            "generated_at": now.isoformat(),
        }
