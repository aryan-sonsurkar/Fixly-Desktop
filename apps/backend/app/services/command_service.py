from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class CommandService:
    def __init__(self) -> None:
        self.context = WorkspaceContext()
        self.ai_service = AIService()
        self.ai_repo = AIRepository()

    async def interpret(self, user_id: str, command: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="quick")
        now = datetime.now(timezone.utc)
        profile = ctx.get("profile", {})
        assignments = ctx.get("assignments", {})

        deadlines_text = "\n".join(
            f"- {d['title']} (Due: {d['due']})"
            for d in assignments.get("deadlines", [])[:10]
        ) or "None"

        prompt_kwargs = {
            "user_command": command,
            "user_name": str(profile.get("name", "Student")),
            "current_time": now.strftime("%H:%M"),
            "timezone": str(ctx.get("timezone", "UTC")),
            "active_assignments": str(assignments.get("total", 0)),
            "deadlines": deadlines_text,
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "streak": str(profile.get("streak", 0)),
            "weekly_hours": str(ctx.get("study", {}).get("total_hours", 0)),
        }

        conv = await self.ai_repo.create_conversation(user_id, f"Command: {command[:50]}")
        prompt = await PromptManager().build(PromptType.SMART_COMMANDS, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)
        content = result["message"]["content"]

        command_type, confidence = self._parse_response(content)

        return {
            "content": content,
            "command_type": command_type,
            "confidence": confidence,
            "generated_at": now.isoformat(),
        }

    def _parse_response(self, content: str) -> tuple[str, float]:
        import re
        type_match = re.search(r'"command_type"\s*:\s*"(\w+)"', content)
        conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', content)
        cmd_type = type_match.group(1) if type_match else "custom"
        confidence = float(conf_match.group(1)) if conf_match else 0.0
        return cmd_type, min(1.0, max(0.0, confidence))
