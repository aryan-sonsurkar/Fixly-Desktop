from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class SubjectRepository:
    async def list_subjects(self, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("subjects")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_subject(self, subject_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def create_subject(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        data = {"user_id": user_id, **payload}
        response = client.table("subjects").insert(data).single().execute()  # type: ignore[attr-defined]
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data") or result

    async def update_subject(
        self, subject_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("subjects")
            .update(updates)
            .eq("id", subject_id)
            .eq("user_id", user_id)
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def delete_subject(self, subject_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("subjects").delete().eq("id", subject_id).eq("user_id", user_id).execute()

    async def count_subjects(self, user_id: str) -> int:
        client = get_supabase()
        response = (
            client.table("subjects")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .execute()
        )
        count = response.count if hasattr(response, "count") else 0
        return count or 0
