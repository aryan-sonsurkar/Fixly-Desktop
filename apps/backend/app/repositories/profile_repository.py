from typing import Any

from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase, get_supabase_for_user

logger = get_logger(__name__)


class ProfileRepository:

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self._client_instance: Client | None = None

    @property
    def _client(self) -> Client:
        if self._client_instance is None:
            self._client_instance = (
                get_supabase_for_user(self.access_token)
                if self.access_token
                else get_supabase()
            )
        return self._client_instance

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        client = self._client
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        response = client.table("profiles").update(updates).eq("id", user_id).execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_settings(self, user_id: str) -> dict[str, Any] | None:
        client = self._client
        response = client.table("settings").select("*").eq("user_id", user_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def upsert_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        payload = {"user_id": user_id, **updates}
        response = (
            client.table("settings")
            .upsert(payload, on_conflict="user_id")

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data
