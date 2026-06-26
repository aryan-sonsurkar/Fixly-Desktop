from typing import Any

from app.core.exceptions import FixlyError
from app.core.logging import get_logger
from app.repositories.profile_repository import ProfileRepository

logger = get_logger(__name__)


class ProfileService:
    def __init__(self) -> None:
        self.repository = ProfileRepository()

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        profile = await self.repository.get_profile(user_id)
        if not profile:
            raise FixlyError("Profile not found")
        return profile

    async def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in updates.items() if v is not None}
        if not clean:
            return await self.repository.get_profile(user_id) or {}
        return await self.repository.update_profile(user_id, clean)

    async def get_settings(self, user_id: str) -> dict[str, Any]:
        settings = await self.repository.get_settings(user_id)
        if not settings:
            return self._default_settings()
        return settings

    async def update_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in updates.items() if v is not None}
        if not clean:
            return await self.get_settings(user_id)
        return await self.repository.upsert_settings(user_id, clean)

    async def complete_onboarding(
        self,
        user_id: str,
        profile_updates: dict[str, Any],
        settings_updates: dict[str, Any],
    ) -> dict[str, Any]:
        profile_updates["onboarding_completed"] = True
        profile_updates.pop("id", None)
        await self.repository.update_profile(user_id, profile_updates)
        if settings_updates:
            settings_updates.pop("user_id", None)
            await self.repository.upsert_settings(user_id, settings_updates)
        profile = await self.repository.get_profile(user_id)
        settings = await self.repository.get_settings(user_id)
        return {
            "profile": profile or {},
            "settings": settings or self._default_settings(),
        }

    async def check_onboarding(self, user_id: str) -> dict[str, bool]:
        profile = await self.repository.get_profile(user_id)
        completed = profile.get("onboarding_completed", False) if profile else False
        return {"onboarding_completed": completed}

    def _default_settings(self) -> dict[str, Any]:
        return {
            "theme": "dark",
            "daily_goal_hours": 0,
            "pomodoro_focus": 25,
            "pomodoro_break": 5,
            "notification_enabled": True,
            "assignment_reminders": True,
            "daily_briefing": True,
            "email_monitoring": False,
            "email_sync_enabled": False,
        }
