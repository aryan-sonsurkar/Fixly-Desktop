from typing import Any

from app.core.logging import get_logger
from app.repositories.pomodoro_repository import PomodoroRepository
from app.services.study_service import StudyService

logger = get_logger(__name__)


class PomodoroService:
    def __init__(self) -> None:
        self.repository = PomodoroRepository()
        self.study_service = StudyService()

    async def get_settings(self, user_id: str) -> dict[str, Any]:
        settings = await self.repository.get_settings(user_id)
        if not settings:
            return {
                "focus_duration": 25,
                "short_break_duration": 5,
                "long_break_duration": 15,
                "long_break_interval": 4,
                "daily_goal": 8,
                "auto_start_breaks": False,
                "auto_start_focus": False,
                "sound_enabled": True,
                "ticking_sound": False,
                "desktop_notifications": True,
            }
        return settings

    async def update_settings(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "focus_duration",
            "short_break_duration",
            "long_break_duration",
            "long_break_interval",
            "daily_goal",
            "auto_start_breaks",
            "auto_start_focus",
            "sound_enabled",
            "ticking_sound",
            "desktop_notifications",
        }
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return await self.get_settings(user_id)
        await self.repository.upsert_settings(user_id, updates)
        return await self.get_settings(user_id)

    async def complete_session(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        session = await self.repository.create_session(user_id, data)

        points = 10 * data.get("cycles_completed", 1)
        try:
            await self.study_service.log_session(user_id, {
                "activity_type": "pomodoro",
                "duration_minutes": data.get("total_focus_minutes", 0),
                "subject_id": data.get("subject_id"),
                "metadata": {
                    "cycles_completed": data.get("cycles_completed", 1),
                    "focus_duration": data.get("focus_duration", 25),
                    "break_duration": data.get("break_duration", 5),
                    "interruptions": data.get("interruptions", 0),
                    "pomodoro_session_id": session.get("id"),
                    "points_override": points,
                },
            })
        except Exception as e:
            logger.error(f"Failed to log study session for pomodoro: {e}")

        return session

    async def get_analytics(self, user_id: str) -> dict[str, Any]:
        return await self.repository.get_analytics(user_id)

    async def get_sessions_for_date(self, user_id: str, session_date: str) -> list[dict[str, Any]]:
        return await self.repository.get_sessions_for_date(user_id, session_date)
