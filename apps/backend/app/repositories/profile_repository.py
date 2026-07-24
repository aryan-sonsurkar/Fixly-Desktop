from typing import Any

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class ProfileRepository:
    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = client.table("profiles").update(updates).eq("id", user_id).execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_settings(self, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = client.table("settings").select("*").eq("user_id", user_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def upsert_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        payload = {"user_id": user_id, **updates}
        response = (
            client.table("settings")
            .upsert(payload, on_conflict="user_id")

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data
