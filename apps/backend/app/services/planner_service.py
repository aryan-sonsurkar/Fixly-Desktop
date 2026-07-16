import json
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ValidationError as FixlyValidationError
from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.study_repository import StudyRepository
from app.schemas.planner import GeneratedScheduleItem
from app.services.ai_service import AIService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class PlannerService:
    def __init__(self) -> None:
        self.assignment_repo = AssignmentRepository()
        self.ai_service = AIService()
        self.ai_repo = AIRepository()
        self.pomodoro_repo = PomodoroRepository()
        self.study_repo = StudyRepository()
        self.context = WorkspaceContext()

    def _validate_schedule_items(self, content: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise FixlyValidationError(
                detail=f"AI response is not valid JSON: {e}"
            )

        if isinstance(data, dict):
            items = data.get("schedule_items")
        elif isinstance(data, list):
            items = data
        else:
            raise FixlyValidationError(
                detail="AI response must be a JSON array or an object with a 'schedule_items' key"
            )

        if not isinstance(items, list):
            raise FixlyValidationError(
                detail="AI response does not contain a valid list of schedule items"
            )

        validated: list[dict[str, Any]] = []
        errors: list[str] = []
        for i, item in enumerate(items):
            try:
                validated.append(GeneratedScheduleItem(**item).model_dump())
            except Exception as e:
                errors.append(f"Item {i}: {e}")

        if errors:
            raise FixlyValidationError(
                detail=f"Schedule item validation failed: {'; '.join(errors)}"
            )

        return validated

    async def generate_daily_plan(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="planner")
        now = datetime.now(timezone.utc)

        prompt_kwargs = {
            "plan_type": "daily",
            "user_name": ctx.get("profile", {}).get("name", "Student"),
            "subjects": ", ".join(s.get("name", "") for s in ctx.get("subjects", [])),
            "active_assignments": str(ctx.get("assignments", {}).get("total", 0)),
            "today_focus_minutes": str(ctx.get("pomodoro", {}).get("today_focus_minutes", 0)),
            "weekly_cycles": str(ctx.get("pomodoro", {}).get("weekly_cycles", 0)),
            "streak": str(ctx.get("profile", {}).get("streak", 0)),
            "xp": str(ctx.get("profile", {}).get("xp", 0)),
        }

        deadlines = ctx.get("assignments", {}).get("deadlines", [])
        if deadlines:
            deadline_text = "\n".join(
                f"- {d['title']} (Due: {d['due']}, Priority: {d['priority']})"
                for d in deadlines[:10]
            )
            prompt_kwargs["deadlines"] = deadline_text
        else:
            prompt_kwargs["deadlines"] = "No upcoming deadlines."

        conv = await self.ai_repo.create_conversation(user_id, "Daily Plan")
        prompt = await PromptManager().build(PromptType.PLANNER, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        schedule_items = self._validate_schedule_items(content)

        plan = {
            "plan_type": "daily",
            "content": content,
            "schedule_items": schedule_items,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
            "context_summary": {
                "active_assignments": ctx.get("assignments", {}).get("total", 0),
                "unread_emails": ctx.get("email", {}).get("unread", 0),
                "today_focus_minutes": ctx.get("pomodoro", {}).get("today_focus_minutes", 0),
                "streak": ctx.get("profile", {}).get("streak", 0),
            },
        }
        return plan

    async def generate_weekly_plan(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="planner")
        now = datetime.now(timezone.utc)

        prompt_kwargs = {
            "plan_type": "weekly",
            "user_name": ctx.get("profile", {}).get("name", "Student"),
            "subjects": ", ".join(s.get("name", "") for s in ctx.get("subjects", [])),
            "active_assignments": str(ctx.get("assignments", {}).get("total", 0)),
            "weekly_cycles": str(ctx.get("pomodoro", {}).get("weekly_cycles", 0)),
            "total_study_hours": str(ctx.get("study", {}).get("total_hours", 0)),
            "streak": str(ctx.get("profile", {}).get("streak", 0)),
        }

        deadlines = ctx.get("assignments", {}).get("deadlines", [])
        if deadlines:
            deadline_text = "\n".join(
                f"- {d['title']} (Due: {d['due']}, Priority: {d['priority']})"
                for d in deadlines[:15]
            )
            prompt_kwargs["deadlines"] = deadline_text
        else:
            prompt_kwargs["deadlines"] = "No upcoming deadlines."

        conv = await self.ai_repo.create_conversation(user_id, "Weekly Plan")
        prompt = await PromptManager().build(PromptType.PLANNER, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        schedule_items = self._validate_schedule_items(content)

        return {
            "plan_type": "weekly",
            "content": content,
            "schedule_items": schedule_items,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
        }

    async def generate_revision_plan(self, user_id: str, subject_ids: list[str] | None = None) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="planner")
        now = datetime.now(timezone.utc)

        subjects = ctx.get("subjects", [])
        if subject_ids:
            subjects = [s for s in subjects if s.get("id") in subject_ids]

        subject_names = ", ".join(s.get("name", "") for s in subjects)
        if not subject_names:
            subject_names = "All subjects"

        prompt_kwargs = {
            "plan_type": "revision",
            "user_name": ctx.get("profile", {}).get("name", "Student"),
            "subjects": subject_names,
            "active_assignments": str(ctx.get("assignments", {}).get("total", 0)),
            "total_study_hours": str(ctx.get("study", {}).get("total_hours", 0)),
            "streak": str(ctx.get("profile", {}).get("streak", 0)),
            "xp": str(ctx.get("profile", {}).get("xp", 0)),
        }

        deadlines = ctx.get("assignments", {}).get("deadlines", [])
        if deadlines:
            deadline_text = "\n".join(
                f"- {d['title']} (Due: {d['due']})" for d in deadlines[:10]
            )
            prompt_kwargs["deadlines"] = deadline_text
        else:
            prompt_kwargs["deadlines"] = "No deadlines."

        conv = await self.ai_repo.create_conversation(user_id, "Revision Plan")
        prompt = await PromptManager().build(PromptType.PLANNER, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        schedule_items = self._validate_schedule_items(content)

        return {
            "plan_type": "revision",
            "content": content,
            "schedule_items": schedule_items,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
        }
