import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ValidationError as FixlyValidationError
from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.study_repository import StudyRepository
from app.schemas.planner import (
    CreateStudySessionAction,
    CreateTaskAction,
    GeneratedScheduleItem,
    PrioritizeTaskAction,
    RescheduleTaskAction,
    ScheduleTaskAction,
)
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

    # Global execution cache for duplicate protection and idempotency
    _executed_actions: dict[str, dict[str, Any]] = {}

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
        if "```" in s:
            import re as _re
            fence = _re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s)
            if fence:
                s = fence.group(1).strip()
        if not s.startswith(("{", "[")):
            import re as _re
            m = _re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
            if m:
                s = m.group(1).strip()
        return s

    @staticmethod
    def _looks_like_json(content: str) -> bool:
        """True when the model attempted a JSON payload (vs free prose)."""
        s = content.strip()
        if s.startswith(("```", "{", "[")):
            return True
        import re as _re
        return bool(_re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s))

    @staticmethod
    def _normalize_schedule_item(item: Any) -> dict[str, Any]:
        """Coerce safe near-misses (case/whitespace) before strict validation.

        Values that echo the option list itself ("low|medium|high|urgent")
        cannot be meaningfully inferred and are left for strict validation
        to reject.
        """
        if not isinstance(item, dict):
            return item
        norm = dict(item)
        for key in ("priority", "type"):
            value = norm.get(key)
            if isinstance(value, str):
                norm[key] = value.strip().lower()
        return norm

    @staticmethod
    def _normalize_action(action: Any) -> dict[str, Any] | None:
        """Normalize an action dictionary and enforce required action_id."""
        if not isinstance(action, dict):
            return None
        norm = dict(action)
        act_type = norm.get("action")
        if not isinstance(act_type, str):
            return None
        act_type = act_type.strip().lower()
        if act_type not in (
            "create_task",
            "schedule_task",
            "create_study_session",
            "reschedule_task",
            "prioritize_task",
        ):
            return None
        norm["action"] = act_type

        # Ensure unique action_id if missing
        if not norm.get("action_id") or not isinstance(norm.get("action_id"), str):
            norm["action_id"] = f"act_{uuid.uuid4().hex[:10]}"

        # Normalize priority if present
        if "priority" in norm:
            val = norm["priority"]
            if isinstance(val, str):
                norm["priority"] = val.strip().lower()

        # Normalize type if present
        if "type" in norm:
            val = norm["type"]
            if isinstance(val, str):
                norm["type"] = val.strip().lower()

        # Normalize duration/estimated minutes
        for min_key in ("duration_minutes", "estimated_minutes"):
            if min_key in norm and norm[min_key] is not None:
                try:
                    norm[min_key] = int(norm[min_key])
                except (ValueError, TypeError):
                    norm[min_key] = None

        return norm

    def _validate_schedule_items(self, content: str) -> list[dict[str, Any]]:
        """Validate legacy or direct schedule items payload."""
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
                validated.append(GeneratedScheduleItem(**self._normalize_schedule_item(item)).model_dump())
            except Exception as e:
                errors.append(f"Item {i}: {e}")

        if errors:
            logger.warning("Planner: dropping %d invalid schedule item(s): %s", len(errors), "; ".join(errors))

        if not validated:
            detail = "; ".join(errors) if errors else "no schedule items found"
            raise FixlyValidationError(
                detail=f"AI response contains no usable schedule items: {detail}"
            )

        return validated

    @staticmethod
    def _synthesize_actions_from_schedule(schedule_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Synthesize actionable structured cards from schedule items."""
        actions: list[dict[str, Any]] = []
        for item in schedule_items:
            itype = item.get("type", "study")
            title = item.get("title", "Study Session")
            priority = item.get("priority", "medium")
            start_t = item.get("start_time", "")
            end_t = item.get("end_time", "")
            aid = f"act_{uuid.uuid4().hex[:10]}"
            if itype == "study":
                actions.append({
                    "action": "create_study_session",
                    "action_id": aid,
                    "title": title,
                    "duration_minutes": 45,
                    "scheduled_time": start_t,
                    "priority": priority,
                })
            elif itype == "assignment":
                actions.append({
                    "action": "create_task",
                    "action_id": aid,
                    "title": title,
                    "description": item.get("description", ""),
                    "priority": priority,
                    "due_date": end_t or None,
                    "estimated_minutes": 45,
                })
            else:
                actions.append({
                    "action": "schedule_task",
                    "action_id": aid,
                    "title": title,
                    "start_time": start_t,
                    "end_time": end_t,
                    "priority": priority,
                    "type": itype,
                })
        return actions

    @staticmethod
    def _synthesize_schedule_from_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Synthesize timeline schedule items from scheduled actions."""
        items: list[dict[str, Any]] = []
        for act in actions:
            act_type = act.get("action")
            if act_type == "schedule_task":
                items.append({
                    "title": act.get("title", "Scheduled Task"),
                    "description": "",
                    "start_time": act.get("start_time", ""),
                    "end_time": act.get("end_time", ""),
                    "priority": act.get("priority", "medium"),
                    "type": act.get("type", "study"),
                })
            elif act_type == "create_study_session" and act.get("scheduled_time"):
                items.append({
                    "title": act.get("title", "Study Session"),
                    "description": f"Focus session ({act.get('duration_minutes', 25)}m)",
                    "start_time": act.get("scheduled_time", ""),
                    "end_time": act.get("scheduled_time", ""),
                    "priority": act.get("priority", "medium"),
                    "type": "study",
                })
        return items

    def validate_and_parse_plan_output(self, content: str) -> dict[str, Any]:
        """Validate and normalize planner output into canonical application state.

        Never returns raw JSON string in 'content' or 'explanation'.
        """
        if not self._looks_like_json(content):
            clean = content.strip()
            return {
                "explanation": clean,
                "actions": [],
                "schedule_items": [],
                "content": clean,
            }

        raw = self._extract_json(content)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise FixlyValidationError(
                detail=f"AI response is not valid JSON: {e}"
            )

        if not isinstance(data, (dict, list)):
            raise FixlyValidationError(
                detail="AI response must be a JSON array or object"
            )

        if isinstance(data, list):
            raw_actions = data
            raw_schedule = data
            raw_explanation = ""
        else:
            raw_actions = data.get("actions") or []
            raw_schedule = data.get("schedule_items") or []
            raw_explanation = data.get("explanation") or ""

        # Validate actions
        validated_actions: list[dict[str, Any]] = []
        if isinstance(raw_actions, list):
            for a in raw_actions:
                norm_a = self._normalize_action(a)
                if not norm_a:
                    continue
                act_type = norm_a.get("action")
                try:
                    if act_type == "create_task":
                        validated_actions.append(CreateTaskAction(**norm_a).model_dump())
                    elif act_type == "schedule_task":
                        validated_actions.append(ScheduleTaskAction(**norm_a).model_dump())
                    elif act_type == "create_study_session":
                        validated_actions.append(CreateStudySessionAction(**norm_a).model_dump())
                    elif act_type == "reschedule_task":
                        validated_actions.append(RescheduleTaskAction(**norm_a).model_dump())
                    elif act_type == "prioritize_task":
                        validated_actions.append(PrioritizeTaskAction(**norm_a).model_dump())
                except Exception as e:
                    logger.warning("Planner: dropping invalid action (%s): %s", act_type, e)

        # Validate schedule items
        validated_schedule: list[dict[str, Any]] = []
        if isinstance(raw_schedule, list):
            for item in raw_schedule:
                norm_item = self._normalize_schedule_item(item)
                try:
                    validated_schedule.append(GeneratedScheduleItem(**norm_item).model_dump())
                except Exception as e:
                    logger.warning("Planner: dropping invalid schedule item: %s", e)

        # Cross-synthesize for complete representation
        if validated_schedule and not validated_actions:
            validated_actions = self._synthesize_actions_from_schedule(validated_schedule)
        elif validated_actions and not validated_schedule:
            validated_schedule = self._synthesize_schedule_from_actions(validated_actions)

        if not validated_actions and not validated_schedule:
            raise FixlyValidationError(
                detail="AI response contains no usable schedule items or actions"
            )

        if isinstance(raw_explanation, str) and raw_explanation.strip():
            explanation = raw_explanation.strip()
        else:
            explanation = "Here is your study plan with recommended actions based on your current workload."

        return {
            "explanation": explanation,
            "actions": validated_actions,
            "schedule_items": validated_schedule,
            "content": explanation,  # Safe prose, never raw JSON
        }

    def parse_and_validate_stored_plan(self, content: str) -> dict[str, Any]:
        """Safely parse stored plan content, guaranteeing zero raw JSON display."""
        try:
            return self.validate_and_parse_plan_output(content)
        except Exception:
            clean = content.strip()
            if self._looks_like_json(clean):
                clean = "Study plan from conversation history."
            return {
                "explanation": clean,
                "actions": [],
                "schedule_items": [],
                "content": clean,
            }

    async def execute_action(
        self,
        user_id: str,
        action_data: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Execute a structured planner action safely with duplicate protection."""
        action_id = action_data.get("action_id") or ""
        key = f"{user_id}:{idempotency_key or action_id}"

        # Idempotency check: duplicate protection
        if key in self._executed_actions:
            logger.info("PlannerService.execute_action: returning idempotent cached result for key %s", key)
            return self._executed_actions[key]

        norm = self._normalize_action(action_data)
        if not norm:
            raise FixlyValidationError(detail=f"Invalid or unsupported action payload: {action_data}")

        act_type = norm.get("action")
        try:
            if act_type == "create_task":
                validated = CreateTaskAction(**norm)
                from app.services.assignment_service import AssignmentService
                svc = AssignmentService(access_token=self.access_token)
                created = await svc.create_assignment(user_id, {
                    "title": validated.title,
                    "description": validated.description or None,
                    "priority": validated.priority,
                    "due_date": validated.due_date,
                    "estimated_study_time": validated.estimated_minutes,
                    "subject_id": validated.subject_id,
                })
                res = {
                    "success": True,
                    "action_id": validated.action_id,
                    "action": "create_task",
                    "message": f"Created task: {validated.title}",
                    "result_data": created if isinstance(created, dict) else {},
                }
            elif act_type == "schedule_task":
                validated = ScheduleTaskAction(**norm)
                from app.services.assignment_service import AssignmentService
                svc = AssignmentService(access_token=self.access_token)
                if validated.task_id:
                    updated = await svc.update_assignment(validated.task_id, user_id, {
                        "due_date": validated.end_time,
                        "priority": validated.priority,
                    })
                    res = {
                        "success": True,
                        "action_id": validated.action_id,
                        "action": "schedule_task",
                        "message": f"Scheduled task: {validated.title}",
                        "result_data": updated if isinstance(updated, dict) else {},
                    }
                else:
                    created = await svc.create_assignment(user_id, {
                        "title": validated.title,
                        "due_date": validated.end_time,
                        "priority": validated.priority,
                        "description": f"Scheduled for {validated.start_time} - {validated.end_time}",
                    })
                    res = {
                        "success": True,
                        "action_id": validated.action_id,
                        "action": "schedule_task",
                        "message": f"Scheduled: {validated.title}",
                        "result_data": created if isinstance(created, dict) else {},
                    }
            elif act_type == "create_study_session":
                validated = CreateStudySessionAction(**norm)
                res = {
                    "success": True,
                    "action_id": validated.action_id,
                    "action": "create_study_session",
                    "message": f"Study session ready: {validated.title} ({validated.duration_minutes}m)",
                    "result_data": {
                        "title": validated.title,
                        "duration_minutes": validated.duration_minutes,
                        "priority": validated.priority,
                        "scheduled_time": validated.scheduled_time,
                        "subject_id": validated.subject_id,
                    },
                }
            elif act_type == "reschedule_task":
                validated = RescheduleTaskAction(**norm)
                from app.services.assignment_service import AssignmentService
                svc = AssignmentService(access_token=self.access_token)
                task_id = validated.task_id
                if not task_id:
                    listing = await svc.list_assignments(user_id, {"search": validated.title})
                    items = listing.get("data", []) if isinstance(listing, dict) else []
                    if items:
                        task_id = items[0].get("id")
                if not task_id:
                    # Never invent state: rescheduling a task that does not
                    # exist must fail loudly instead of creating an unrelated
                    # assignment.
                    raise FixlyValidationError(
                        detail=f"No matching task found for reschedule: '{validated.title}'"
                    )
                updated = await svc.update_assignment(str(task_id), user_id, {"due_date": validated.new_start_time})
                res = {
                    "success": True,
                    "action_id": validated.action_id,
                    "action": "reschedule_task",
                    "message": f"Rescheduled: {validated.title}",
                    "result_data": updated if isinstance(updated, dict) else {},
                }
            elif act_type == "prioritize_task":
                validated = PrioritizeTaskAction(**norm)
                from app.services.assignment_service import AssignmentService
                svc = AssignmentService(access_token=self.access_token)
                task_id = validated.task_id
                if not task_id:
                    listing = await svc.list_assignments(user_id, {"search": validated.title})
                    items = listing.get("data", []) if isinstance(listing, dict) else []
                    if items:
                        task_id = items[0].get("id")
                if not task_id:
                    # Never invent state: reprioritizing a task that does not
                    # exist must fail loudly instead of creating one.
                    raise FixlyValidationError(
                        detail=f"No matching task found to prioritize: '{validated.title}'"
                    )
                updated = await svc.update_assignment(str(task_id), user_id, {"priority": validated.priority})
                res = {
                    "success": True,
                    "action_id": validated.action_id,
                    "action": "prioritize_task",
                    "message": f"Updated priority for: {validated.title} to {validated.priority}",
                    "result_data": updated if isinstance(updated, dict) else {},
                }
            else:
                raise FixlyValidationError(detail=f"Unknown action type: {act_type}")
        except Exception as e:
            logger.error("PlannerService.execute_action failed: %s", e)
            raise

        self._executed_actions[key] = res
        return res

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
            parsed = self.validate_and_parse_plan_output(content)
            explanation = parsed["explanation"]
            actions = parsed["actions"]
            schedule_items = parsed["schedule_items"]
        except FixlyValidationError as ve:
            if self._looks_like_json(content):
                try:
                    await self.ai_repo.delete_conversation(conv["id"], user_id)
                except Exception:
                    pass
                raise
            logger.warning("Planner daily: strict JSON failed, returning text plan: %s", ve.detail)
            explanation = content
            actions = []
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

        plan = {
            "plan_type": "daily",
            "explanation": explanation,
            "actions": actions,
            "schedule_items": schedule_items,
            "content": explanation,
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
            parsed = self.validate_and_parse_plan_output(content)
            explanation = parsed["explanation"]
            actions = parsed["actions"]
            schedule_items = parsed["schedule_items"]
        except FixlyValidationError as ve:
            if self._looks_like_json(content):
                try:
                    await self.ai_repo.delete_conversation(conv["id"], user_id)
                except Exception:
                    pass
                raise
            logger.warning("Planner weekly: strict JSON failed, returning text plan: %s", ve.detail)
            explanation = content
            actions = []
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

        return {
            "plan_type": "weekly",
            "explanation": explanation,
            "actions": actions,
            "schedule_items": schedule_items,
            "content": explanation,
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
            parsed = self.validate_and_parse_plan_output(content)
            explanation = parsed["explanation"]
            actions = parsed["actions"]
            schedule_items = parsed["schedule_items"]
        except FixlyValidationError as ve:
            if self._looks_like_json(content):
                try:
                    await self.ai_repo.delete_conversation(conv["id"], user_id)
                except Exception:
                    pass
                raise
            logger.warning("Planner revision: strict JSON failed, returning text plan: %s", ve.detail)
            explanation = content
            actions = []
            schedule_items = []
        except Exception:
            try:
                await self.ai_repo.delete_conversation(conv["id"], user_id)
            except Exception:
                pass
            raise

        return {
            "plan_type": "revision",
            "explanation": explanation,
            "actions": actions,
            "schedule_items": schedule_items,
            "content": explanation,
            "conversation_id": conv["id"],
            "generated_at": now.isoformat(),
        }

    # ── Daily briefing (dashboard card, not chat) ─────────────────────

    def _fallback_quote(self, date_str: str) -> str:
        from app.services.daily_briefing_service import DailyBriefingService
        return DailyBriefingService(access_token=self.access_token)._fallback_quote(date_str)

    def _fallback_motivation(
        self, items: list[dict[str, Any]], summary_ctx: dict[str, Any]
    ) -> str:
        from app.services.daily_briefing_service import DailyBriefingService
        return DailyBriefingService(access_token=self.access_token)._fallback_motivation(items, summary_ctx)

    def _sanitize_quote(self, text: str) -> str:
        from app.services.daily_briefing_service import DailyBriefingService
        return DailyBriefingService(access_token=self.access_token)._sanitize_quote(text)

    def _parse_narrative(self, content: str) -> dict[str, str] | None:
        from app.services.daily_briefing_service import DailyBriefingService
        return DailyBriefingService(access_token=self.access_token)._parse_narrative(content)

    async def generate_daily_briefing(self, user_id: str) -> dict[str, Any]:
        """Compose the dashboard Daily Briefing from real workspace data.

        Delegates to DailyBriefingService which runs via non-chat direct LLM
        generation without creating conversations or persisting chat messages.
        """
        from app.services.daily_briefing_service import DailyBriefingService
        service = DailyBriefingService(access_token=self.access_token)
        return await service.generate_daily_briefing(user_id)
