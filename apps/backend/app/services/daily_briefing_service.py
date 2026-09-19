import json
import re
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.repositories.ai_repository import AIRepository
from app.schemas.planner import DailyBriefingResponse, GeneratedScheduleItem
from app.services.ai_service import AIService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class DailyBriefingService:
    """Dedicated service for Dashboard Daily Briefing.

    Uses the existing AI engine/context infrastructure via a non-chat direct
    generation path: NO conversation is created, NO chat messages are persisted,
    and internal prompts never contaminate AI Workspace.
    """

    FALLBACK_QUOTES = [
        "Small daily improvements over time lead to stunning academic results.",
        "Consistency beats intensity. One focused session today moves everything forward.",
        "The secret to getting ahead is simply getting started on your top task.",
        "Focus on the process, and the academic grades will naturally follow.",
        "You do not have to be great to start, but you have to start to be great.",
        "Every 25 minutes of deep focus is an investment in your future self.",
        "Study with intention. Master one concept before moving to the next.",
    ]

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.context = WorkspaceContext(access_token=access_token)
        self.ai_service = AIService(access_token=access_token)
        self.ai_repo = AIRepository(access_token=access_token)

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
        for sep in ("—", "--", "- "):
            if sep in clean:
                clean = clean.split(sep)[0].strip().strip('"').strip("'")
        return clean or self.FALLBACK_QUOTES[0]

    def _extract_json(self, text: str) -> str:
        s = text.strip()
        if s.startswith("```"):
            lines = s.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        if not s.startswith(("{", "[")):
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
            if m:
                s = m.group(1).strip()
        return s

    def _parse_narrative(self, content: str) -> dict[str, str] | None:
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

    def _build_focus_items_from_context(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        """Construct grounded focus items from real assignments and deadlines."""
        deadlines = ctx.get("assignments", {}).get("deadlines", [])
        focus_items: list[dict[str, Any]] = []

        start_hours = [9, 11, 14, 16]
        for idx, d in enumerate(deadlines[:4]):
            sh = start_hours[idx % len(start_hours)]
            eh = sh + 1
            start_str = f"{sh:02d}:00"
            end_str = f"{eh:02d}:00"
            item = {
                "title": f"Work on {d.get('title', 'Assignment')}",
                "description": f"Due {d.get('due', 'soon')}. Focus on core deliverables.",
                "start_time": start_str,
                "end_time": end_str,
                "priority": (
                    d.get("priority", "medium")
                    if d.get("priority") in ("low", "medium", "high", "urgent")
                    else "medium"
                ),
                "type": "assignment",
            }
            try:
                focus_items.append(GeneratedScheduleItem(**item).model_dump())
            except Exception:
                pass

        if not focus_items:
            subjects = ctx.get("subjects", [])
            sub_name = subjects[0].get("name", "Key Subject") if subjects else "Study Session"
            fallback_item = {
                "title": f"Review {sub_name}",
                "description": "Deep focus session on concepts and notes.",
                "start_time": "10:00",
                "end_time": "10:50",
                "priority": "medium",
                "type": "study",
            }
            focus_items.append(GeneratedScheduleItem(**fallback_item).model_dump())

        return focus_items

    async def generate_daily_briefing(self, user_id: str) -> dict[str, Any]:
        """Compose the Dashboard Daily Briefing without creating or saving any chat conversation."""
        now = datetime.now(timezone.utc)
        date_str = now.date().isoformat()

        ctx = await self.context.gather(user_id, budget="briefing")
        items = self._build_focus_items_from_context(ctx)

        summary_ctx = {
            "user_name": ctx.get("profile", {}).get("name", "Student"),
            "active_assignments": ctx.get("assignments", {}).get("total", 0),
            "unread_emails": ctx.get("email", {}).get("unread", 0),
            "today_focus_minutes": ctx.get("pomodoro", {}).get("today_focus_minutes", 0),
            "streak": ctx.get("profile", {}).get("streak", 0),
        }
        user_name = str(summary_ctx.get("user_name", "Student"))

        narrative: dict[str, str] | None = None
        ai_available = True
        try:
            item_lines = "\n".join(
                f"- {i.get('title', 'Task')} ("
                f"{i.get('start_time', '?')}–{i.get('end_time', '?')}, "
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
            # Direct non-chat generation: no conversation created, no message persisted.
            raw_response = await self.ai_service.generate_text(
                user_id=user_id,
                prompt=prompt,
                system_prompt="You are Fixly AI, a focused academic assistant. Output only the requested JSON.",
                max_tokens=400,
                temperature=0.5,
            )
            narrative = self._parse_narrative(raw_response)
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

        # Keep the dashboard boundary schema-validated even when the model
        # falls back, so raw provider output can never leak into the UI.
        return DailyBriefingResponse(
            date=date_str,
            greeting=greeting,
            summary=summary,
            focus_items=items,
            quote={"text": quote_text, "attribution": "Fixly AI"},
            motivation=motivation,
            next_action=next_action,
            ai_available=ai_available,
            generated_at=now.isoformat(),
        ).model_dump()

    async def cleanup_leaked_conversations(self, user_id: str) -> int:
        """Safely delete internal Daily Briefing residue conversations.

        Only removes conversations named 'Daily Plan' that contain internal
        briefing prompts. User-created conversations remain completely untouched.
        """
        cleaned = 0
        try:
            convs = await self.ai_repo.list_conversations(user_id)
            for c in convs:
                if c.get("title") == "Daily Plan":
                    msgs = await self.ai_repo.get_messages(c["id"])
                    has_internal_prompt = any(
                        "writing a dashboard Daily Briefing" in str(m.get("content", ""))
                        for m in msgs
                    )
                    if has_internal_prompt:
                        await self.ai_repo.delete_conversation(c["id"], user_id)
                        cleaned += 1
                        logger.info("Cleaned up leaked briefing conversation %s for user %s", c["id"], user_id)
        except Exception as e:
            logger.warning("Briefing conversation cleanup failed (non-critical): %s", e)
        return cleaned
