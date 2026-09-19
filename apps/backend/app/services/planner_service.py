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
    # Deterministic fallback quotes: original, unattributed to real people.
    FALLBACK_QUOTES = [
        "Progress is built one focused session at a time.",
        "Start small. A single finished task changes the whole day.",
        "Attention is a skill. Every session trains it.",
        "Done is better than perfect. Begin with the easiest step.",
        "Consistency beats intensity.",
        "Your future self is built by today's smallest effort.",
        "Focus on the next step, not the whole staircase.",
    ]

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.assignment_repo = AssignmentRepository(access_token=access_token)
        self.ai_service = AIService(access_token=access_token)
        self.ai_repo = AIRepository(access_token=access_token)
        self.pomodoro_repo = PomodoroRepository(access_token=access_token)
        self.study_repo = StudyRepository(access_token=access_token)
        self.context = WorkspaceContext(access_token=access_token)

    def _extract_json(self, raw: str) -> str:
        """Strip markdown fences, preamble, and extract the JSON payload."""
        s = raw.strip()
        # Remove ```json ... ``` or ``` ... ```
        if "```" in s:
            # Find first { or [ inside fences
            import re as _re
            fence = _re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s)
            if fence:
                s = fence.group(1).strip()
        # If still not starting with { or [, try to locate JSON object/array
        if not s.startswith(("{", "[")):
            import re as _re
            m = _re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
            if m:
                s = m.group(1).strip()
        return s

    def _validate_schedule_items(self, content: str) -> list[dict[str, Any]]:
        raw = self._extract_json(content)
        try:
            data = json.loads(raw)
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

        if len(items) == 0:
            raise FixlyValidationError(detail="AI returned an empty schedule")

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
        prompt = await PromptManager(access_token=self.access_token).build(
            PromptType.PLANNER, user_id, **prompt_kwargs
        )
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        try:
            schedule_items = self._validate_schedule_items(content)
        except FixlyValidationError as ve:
            # Lenient fallback: AI returned useful text but not strict JSON.
            # Keep the conversation and return content without schedule_items
            # so the user sees the plan instead of an error.
            logger.warning("Planner daily: strict JSON failed, returning text plan: %s", ve.detail)
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

        plan = {
            "plan_type": "daily",
            "content": content,
            "schedule_items": schedule_items,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
            "context_summary": {
                "user_name": ctx.get("profile", {}).get("name", "Student"),
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
        prompt = await PromptManager(access_token=self.access_token).build(
            PromptType.PLANNER, user_id, **prompt_kwargs
        )
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        try:
            schedule_items = self._validate_schedule_items(content)
        except FixlyValidationError as ve:
            logger.warning("Planner weekly: strict JSON failed, returning text plan: %s", ve.detail)
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

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
        prompt = await PromptManager(access_token=self.access_token).build(
            PromptType.PLANNER, user_id, **prompt_kwargs
        )
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        content = result["message"]["content"]
        try:
            schedule_items = self._validate_schedule_items(content)
        except FixlyValidationError as ve:
            logger.warning("Planner revision: strict JSON failed, returning text plan: %s", ve.detail)
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

        return {
            "plan_type": "revision",
            "content": content,
            "schedule_items": schedule_items,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
        }

    # ── Daily briefing (dashboard card, not chat) ─────────────────────

    def _fallback_quote(self, date_str: str) -> str:
        try:
            day_num = int(date_str.replace("-", ""))
        except ValueError:
            day_num = 0
        return self.FALLBACK_QUOTES[day_num % len(self.FALLBACK_QUOTES)]

    def _fallback_motivation(
        self, items: list[dict[str, Any]], summary_ctx: dict[str, Any]
    ) -> str:
        due_today = sum(1 for i in items if str(i.get("priority", "")) in ("high", "urgent"))
        active = int(summary_ctx.get("active_assignments", 0) or 0)
        streak = int(summary_ctx.get("streak", 0) or 0)
        if due_today > 0:
            return (
                f"You have {due_today} high-priority item{'s' if due_today != 1 else ''} today. "
                "Getting one focused session done early will reduce the pressure later."
            )
        if active > 0:
            return (
                f"You have {active} active assignment{'s' if active != 1 else ''}. "
                "Pick the most urgent one and work on it for 25 minutes."
            )
        if streak > 0:
            return (
                f"You're on a {streak}-day streak. "
                "One more focused session today keeps it going."
            )
        return (
            "No urgent deadlines right now. "
            "Use today to review a weak topic for 25 minutes."
        )

    def _sanitize_quote(self, text: str) -> str:
        """Short original quote, never attributed to a real person."""
        clean = text.strip().strip('"').strip("'")[:200]
        # Drop any "— Name" attribution; the only allowed credit is Fixly AI.
        for sep in ("—", "--", "- "):
            if sep in clean:
                clean = clean.split(sep)[0].strip().strip('"').strip("'")
        return clean or self.FALLBACK_QUOTES[0]

    def _parse_narrative(self, content: str) -> dict[str, str] | None:
        """Lenient parse of the briefing narrative JSON. Returns None if unusable."""
        try:
            data = json.loads(self._extract_json(content))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        summary = str(data.get("summary", "")).strip()[:500]
        quote = str(data.get("quote", "")).strip()[:200]
        motivation = str(data.get("motivation", "")).strip()[:400]
        if not summary or not quote or not motivation:
            return None
        return {"summary": summary, "quote": quote, "motivation": motivation}

    async def generate_daily_briefing(self, user_id: str) -> dict[str, Any]:
        """Compose the dashboard Daily Briefing from real workspace data.

        Schedule items always originate from the validated daily plan (never
        invented). One small grounded LLM call adds summary/quote/motivation;
        any failure degrades to a deterministic briefing.
        """
        now = datetime.now(timezone.utc)
        date_str = now.date().isoformat()

        plan = await self.generate_daily_plan(user_id)
        raw_items = plan.get("schedule_items") or []
        items = [dict(i) for i in raw_items][:8]
        summary_ctx: dict[str, Any] = plan.get("context_summary") or {}
        user_name = str(summary_ctx.get("user_name", "Student"))

        narrative: dict[str, str] | None = None
        ai_available = True
        try:
            item_lines = "\n".join(
                f"- {i.get('title', 'Task')} "
                f"({i.get('start_time', '?')}–{i.get('end_time', '?')}, "
                f"{i.get('priority', 'medium')})"
                for i in items
            ) or "(no scheduled items today)"
            prompt = (
                "You are Fixly AI writing a dashboard Daily Briefing. "
                f"Today's validated schedule items (do NOT invent others):\n{item_lines}\n"
                f"Context: {summary_ctx.get('active_assignments', 0)} active assignments, "
                f"{summary_ctx.get('today_focus_minutes', 0)} focus minutes today, "
                f"streak {summary_ctx.get('streak', 0)} days.\n"
                "Reply with ONLY a JSON object (no fences, no preamble) with keys: "
                '"summary" (1-2 sentence overview referencing the listed items), '
                '"quote" (one short original study quote, no author name), '
                '"motivation" (1-3 sentences grounded in the context above).'
            )
            result = await self.ai_service.chat(
                user_id, prompt, plan["conversation_id"], stream=False
            )
            narrative = self._parse_narrative(result["message"]["content"])
            if narrative is None:
                logger.warning("Briefing narrative unparseable, using fallback")
        except Exception as e:
            logger.warning("Briefing narrative generation failed, using fallback: %s", e)
            narrative = None
        if narrative is None:
            ai_available = False

        if narrative:
            summary = narrative["summary"]
            quote_text = self._sanitize_quote(narrative["quote"])
            motivation = narrative["motivation"]
        else:
            first = items[0].get("title", "your top task") if items else "your top task"
            summary = (
                f"Focus on {first} today."
                if items
                else "Nothing scheduled today. Review a weak topic or plan tomorrow."
            )
            quote_text = self._fallback_quote(date_str)
            motivation = self._fallback_motivation(items, summary_ctx)

        next_action = None
        if items:
            next_action = {"label": "Start Focus Session", "target": "pomodoro"}

        hour = now.hour
        greeting = (
            f"Good morning, {user_name}."
            if hour < 12
            else f"Good afternoon, {user_name}."
            if hour < 17
            else f"Good evening, {user_name}."
        )

        return {
            "date": date_str,
            "greeting": greeting,
            "summary": summary,
            "focus_items": items,
            "quote": {"text": quote_text, "attribution": "Fixly AI"},
            "motivation": motivation,
            "next_action": next_action,
            "ai_available": ai_available,
            "generated_at": now.isoformat(),
        }
