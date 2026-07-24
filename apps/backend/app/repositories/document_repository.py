from datetime import datetime, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class DocumentRepository:
    async def create_document(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("documents")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_document(self, document_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("documents")
            .select("*")
            .eq("id", document_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def update_document(
        self, document_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = get_supabase()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("documents")
            .update(updates)
            .eq("id", document_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def delete_document(self, document_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("documents").delete().eq("id", document_id).eq("user_id", user_id).execute()

    async def list_documents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        subject_id: str | None = None,
        status: str | None = None,
        file_type: str | None = None,
        search: str | None = None,
        favorites_only: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        client = get_supabase()

        query = client.table("documents").select("*", count="exact").eq("user_id", user_id)  # type: ignore[arg-type]

        if subject_id:
            query = query.eq("subject_id", subject_id)
        if status:
            query = query.eq("status", status)
        if file_type:
            query = query.eq("file_type", file_type)
        if favorites_only:
            query = query.eq("is_favorite", True)
        if search:
            query = query.ilike("original_name", f"%{search}%")

        query = query.order("created_at", desc=True)

        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        docs = cast(list[dict[str, Any]], data.get("data", []))
        total = response.count or 0
        return docs, total

    async def get_chunks(self, document_id: str, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("document_chunks")
            .select("*")
            .eq("document_id", document_id)
            .eq("user_id", user_id)
            .order("chunk_index")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def create_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        client = get_supabase()
        response = client.table("document_chunks").insert(chunks).execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def delete_chunks(self, document_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("document_chunks").delete().eq("document_id", document_id).eq("user_id", user_id).execute()

    async def create_ocr_result(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("document_ocr_results")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_ocr_result(self, document_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("document_ocr_results")
            .select("*")
            .eq("document_id", document_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def link_conversation(
        self, document_id: str, conversation_id: str, user_id: str
    ) -> dict[str, Any]:
        client = get_supabase()
        payload = {
            "document_id": document_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
        }
        response = (
            client.table("document_conversations")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_conversation_ids(self, document_id: str, user_id: str) -> list[str]:
        client = get_supabase()
        response = (
            client.table("document_conversations")
            .select("conversation_id")
            .eq("document_id", document_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = cast(list[dict[str, Any]], data.get("data", []))
        return [r["conversation_id"] for r in rows]

    async def get_recent_documents(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("documents")
            .select("id, original_name, file_type, status, created_at, page_count, file_size")
            .eq("user_id", user_id)
            .eq("status", "processed")
            .order("last_opened_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))
