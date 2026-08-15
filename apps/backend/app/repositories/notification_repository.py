from datetime import datetime, timezone
from typing import Any, cast

from supabase import Client

from app.core.supabase import get_supabase, get_supabase_for_user


class NotificationRepository:

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

    async def create(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        data = {
            "user_id": user_id,
            **payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.table("notifications").insert(data).execute()
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _raw = raw.get("data") or raw
        return _raw[0] if isinstance(_raw, list) else _raw

    async def list_notifications(
        self, user_id: str, unread_only: bool = False,
        limit: int = 50, offset: int = 0,
        ntype: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        client = self._client
        query = client.table("notifications").select("*", count="exact").eq("user_id", user_id)  # type: ignore[arg-type]
        if unread_only:
            query = query.eq("read", False)
        if ntype:
            query = query.eq("type", ntype)
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        total = response.count or 0
        return items, total

    async def mark_read(self, notification_id: str, user_id: str) -> dict[str, Any] | None:
        client = self._client
        response = (
            client.table("notifications")
            .update({"read": True})
            .eq("id", notification_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        raw = data.get("data")
        if isinstance(raw, list):
            return raw[0] if raw else None
        return raw if isinstance(raw, dict) else None

    async def mark_all_read(self, user_id: str) -> int:
        client = self._client
        now = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("notifications")
            .update({"read": True, "read_at": now})
            .eq("user_id", user_id)
            .eq("read", False)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        return len(items)

    async def delete(self, notification_id: str, user_id: str) -> int:
        client = self._client
        response = (
            client.table("notifications")
            .delete()
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        return len(items)

    async def unread_count(self, user_id: str) -> int:
        client = self._client
        response = (
            client.table("notifications")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .eq("read", False)
            .execute()
        )
        return response.count or 0
