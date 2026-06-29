from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService
from app.services.workspace_context import WorkspaceContext

logger = get_logger(__name__)


class RiskDetectorService:
    def __init__(self) -> None:
        self.context = WorkspaceContext()
        self.ai_service = AIService()
        self.ai_repo = AIRepository()

    async def assess(self, user_id: str) -> dict[str, Any]:
        ctx = await self.context.gather(user_id, budget="copilot")
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        profile = ctx.get("profile", {})
        study = ctx.get("study", {})
        pomo = ctx.get("pomodoro", {})
        email = ctx.get("email", {})
        assignments = ctx.get("assignments", {})

        prompt_kwargs = self._build_kwargs(ctx, today, profile, study, pomo, email, assignments, now)

        conv = await self.ai_repo.create_conversation(user_id, "Risk Assessment")
        prompt = await PromptManager().build(PromptType.RISK_DETECTOR, user_id, **prompt_kwargs)
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)
        content = result["message"]["content"]

        health_score = self._extract_health_score(content, assignments, study, email)
        risk_level = self._calculate_risk_level(health_score)

        return {
            "content": content,
            "risk_level": risk_level,
            "academic_health_score": health_score,
            "generated_at": now.isoformat(),
            "context_summary": {
                "active_assignments": assignments.get("total", 0),
                "overdue_count": assignments.get("overdue_count", 0),
                "study_days": study.get("study_days", 0),
                "weekly_hours": study.get("total_hours", 0),
                "streak": profile.get("streak", 0),
                "unread_notifications": ctx.get("notifications", {}).get("unread_count", 0),
            },
        }

    def _build_kwargs(self, ctx: dict[str, Any], today: str, profile: dict[str, Any],
                      study: dict[str, Any], pomo: dict[str, Any],
                      email: dict[str, Any], assignments: dict[str, Any],
                      now: datetime) -> dict[str, str]:
        overdue_titles = assignments.get("overdue_titles", [])
        return {
            "user_name": str(profile.get("name", "Student")),
            "streak": str(profile.get("streak", 0)),
            "xp": str(profile.get("xp", 0)),
            "active_assignments": str(assignments.get("total", 0)),
            "overdue_count": str(assignments.get("overdue_count", 0)),
            "overdue_titles": ", ".join(overdue_titles) if overdue_titles else "None",
            "urgent_deadlines": ", ".join(assignments.get("urgent_deadlines", [])) or "None",
            "study_days": str(study.get("study_days", 0)),
            "weekly_hours": str(study.get("total_hours", 0)),
            "avg_daily_minutes": str(study.get("avg_daily", 0)),
            "missed_study_days": str(max(0, 7 - study.get("study_days", 0))),
            "last_study_session": "Today" if pomo.get("today_focus_minutes", 0) > 0 else "Not today",
            "weekly_cycles": str(pomo.get("weekly_cycles", 0)),
            "today_focus": str(pomo.get("today_focus_minutes", 0)),
            "unread_emails": str(email.get("unread", 0)),
            "unread_academic": str(email.get("unread", 0)),
            "pending_reviews": str(email.get("pending_review", 0)),
            "unprocessed_docs": str(ctx.get("documents", {}).get("count", 0)),
            "unread_notifications": str(ctx.get("notifications", {}).get("unread_count", 0)),
            "current_time": now.strftime("%H:%M"),
            "timezone": str(ctx.get("timezone", "UTC")),
        }

    def _extract_health_score(self, content: str, assignments: dict[str, Any],
                              study: dict[str, Any], email: dict[str, Any]) -> int:
        import re
        match = re.search(r'"academic_health_score"\s*:\s*(\d+)', content)
        if match:
            return min(100, max(0, int(match.group(1))))
        score = 50
        overdue = assignments.get("overdue_count", 0)
        if overdue == 0:
            score += 15
        elif overdue <= 2:
            score += 5
        else:
            score -= 10
        study_ratio = study.get("study_days", 0) / 7.0
        score += int(study_ratio * 15)
        if email.get("unread", 0) <= 5:
            score += 5
        if email.get("unread", 0) > 20:
            score -= 5
        return min(100, max(0, score))

    def _calculate_risk_level(self, score: int) -> str:
        if score >= 70:
            return "Low"
        if score >= 40:
            return "Medium"
        return "High"
