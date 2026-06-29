from datetime import datetime, timezone
from typing import Any, cast

from app.core.supabase import get_supabase


class NotificationRepository:
    async def create(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        data = {
            "user_id": user_id,
            **payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.table("notifications").insert(data).single().execute()  # type: ignore[attr-defined]
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return raw.get("data") or raw

    async def list_notifications(
        self, user_id: str, unread_only: bool = False,
        limit: int = 50, offset: int = 0,
        ntype: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        client = get_supabase()
        query = client.table("notifications").select("*", count="exact").eq("user_id", user_id)  # type: ignore[arg-type]
        if unread_only:
            query = query.eq("is_read", False)
        if ntype:
            query = query.eq("type", ntype)
        query = query.order("created_at", ascending=False)  # type: ignore[call-arg]
        query = query.range(offset, offset + limit - 1)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        total = response.count or 0
        return items, total

    async def mark_read(self, notification_id: str, user_id: str) -> dict[str, Any]:
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("notifications")
            .update({"is_read": True, "read_at": now})
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def mark_all_read(self, user_id: str) -> int:
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("notifications")
            .update({"is_read": True, "read_at": now})
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        return len(items)

    async def delete(self, notification_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("notifications").delete().eq("id", notification_id).eq("user_id", user_id).execute()

    async def unread_count(self, user_id: str) -> int:
        client = get_supabase()
        response = (
            client.table("notifications")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return response.count or 0
