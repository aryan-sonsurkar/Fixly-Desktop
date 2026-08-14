from typing import Any, cast

from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase, get_supabase_for_user
from app.repositories.utils import single_or_none

logger = get_logger(__name__)


class SubjectRepository:

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

    async def list_subjects(self, user_id: str) -> list[dict[str, Any]]:
        client = self._client
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
        client = self._client
        return single_or_none(
            client.table("subjects")
            .select("*")
            .eq("id", subject_id)
            .eq("user_id", user_id)
        )

    async def create_subject(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        data = {"user_id": user_id, **payload}
        response = client.table("subjects").insert(data).execute()
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = result.get("data") or result
        return _result[0] if isinstance(_result, list) else _result

    async def update_subject(
        self, subject_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = self._client
        response = (
            client.table("subjects")
            .update(updates)
            .eq("id", subject_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def delete_subject(self, subject_id: str, user_id: str) -> None:
        client = self._client
        client.table("subjects").delete().eq("id", subject_id).eq("user_id", user_id).execute()

    async def count_subjects(self, user_id: str) -> int:
        client = self._client
        response = (
            client.table("subjects")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .execute()
        )
        count = response.count if hasattr(response, "count") else 0
        return count or 0
