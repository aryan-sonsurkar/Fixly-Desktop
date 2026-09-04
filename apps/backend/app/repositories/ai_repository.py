import asyncio
from datetime import datetime, timezone
from typing import Any, cast

from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase, get_supabase_for_user
from app.core.threads import run_in_thread
from app.repositories.utils import single_or_none

logger = get_logger(__name__)


class AIRepository:

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

    async def create_conversation(self, user_id: str, title: str = "New conversation") -> dict[str, Any]:
        client = self._client
        response = (
            client.table("conversations")
            .insert({"user_id": user_id, "title": title})

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        client = self._client
        response = (
            client.table("conversations")
            .select("id, title, created_at, updated_at, is_pinned, is_archived")
            .eq("user_id", user_id)
            .order("is_pinned", desc=True)
            .order("updated_at", desc=True)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        convs = cast(list[dict[str, Any]], data.get("data", []))

        counts = await asyncio.gather(
            *(run_in_thread(self.get_message_count, conv["id"]) for conv in convs)
        )
        for conv, count in zip(convs, counts):
            conv["message_count"] = count

        return convs

    async def search_conversations(self, user_id: str, query: str) -> list[dict[str, Any]]:
        client = self._client
        response = (
            client.table("conversations")
            .select("id, title, created_at, updated_at, is_pinned, is_archived")
            .eq("user_id", user_id)
            .ilike("title", f"%{query}%")
            .order("updated_at", desc=True)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        convs = cast(list[dict[str, Any]], data.get("data", []))
        counts = await asyncio.gather(
            *(run_in_thread(self.get_message_count, conv["id"]) for conv in convs)
        )
        for conv, count in zip(convs, counts):
            conv["message_count"] = count
        return convs

    async def get_conversation(self, conversation_id: str, user_id: str) -> dict[str, Any] | None:
        client = self._client
        return single_or_none(
            client.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
        )

    async def update_conversation(self, conversation_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("conversations")
            .update(updates)
            .eq("id", conversation_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        client = self._client
        client.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        client = self._client
        response = (
            client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_messages_bulk(self, conversation_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        if not conversation_ids:
            return {}
        client = self._client
        response = (
            client.table("messages")
            .select("*")
            .in_("conversation_id", conversation_ids)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        msgs = cast(list[dict[str, Any]], data.get("data", []))
        by_conversation: dict[str, list[dict[str, Any]]] = {}
        for m in msgs:
            by_conversation.setdefault(m.get("conversation_id", ""), []).append(m)
        return by_conversation

    async def create_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        provider: str | None = None,
        tokens: int | None = None,
    ) -> dict[str, Any]:
        client = self._client
        payload = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "provider": provider,
            "tokens": tokens,
        }
        response = (
            client.table("messages")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = data.get("data") or data
        result = _result[0] if isinstance(_result, list) else _result

        client.table("conversations").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq(
            "id", conversation_id
        ).execute()

        return result

    async def get_message_count(self, conversation_id: str) -> int:
        client = self._client
        response = (
            client.table("messages")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("conversation_id", conversation_id)
            .execute()
        )
        return response.count or 0

    async def update_message(
        self, message_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        client = self._client
        response = (
            client.table("messages")
            .update(updates)
            .eq("id", message_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        raw = data.get("data")
        if isinstance(raw, list):
            return raw[0] if raw else None
        return raw if isinstance(raw, dict) else None

    async def delete_message(self, message_id: str, user_id: str) -> int:
        client = self._client
        response = (
            client.table("messages")
            .delete()
            .eq("id", message_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        items = cast(list[dict[str, Any]], data.get("data", []))
        return len(items)

    async def get_ai_settings(self, user_id: str) -> dict[str, Any] | None:
        client = self._client

        columns = (
            "preferred_provider, provider_model, temperature, max_tokens, streaming_enabled, "
            "system_prompt, academic_context, conversation_memory, fallback_provider, ai_enabled"
        )
        result = single_or_none(
            client.table("settings")
            .select(columns)
            .eq("user_id", user_id)
        )
        if isinstance(result, dict) and result.get("preferred_provider"):
            result["ollama_available"] = False
            result["gemini_available"] = False
            return result
        return {
            "preferred_provider": "auto",
            "provider_model": None,
            "temperature": 0.7,
            "max_tokens": 2048,
            "streaming_enabled": True,
            "system_prompt": None,
            "academic_context": True,
            "conversation_memory": 50,
            "fallback_provider": "auto",
            "ai_enabled": True,
            "ollama_available": False,
            "gemini_available": False,
        }

    async def update_ai_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        # Filter to known columns to avoid 500 if migration 00013 not yet applied on remote
        allowed = {
            "preferred_provider", "provider_model", "temperature", "max_tokens",
            "streaming_enabled", "system_prompt", "academic_context",
            "conversation_memory", "fallback_provider", "ai_enabled",
        }
        clean = {k: v for k, v in updates.items() if k in allowed}
        # If provider_model column missing on remote, retry without it
        for attempt in (clean, {k: v for k, v in clean.items() if k != "provider_model"}):
            try:
                payload = {"user_id": user_id, **attempt}
                response = (
                    client.table("settings")
                    .upsert(payload, on_conflict="user_id")
                    .execute()
                )
                data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
                _result = data.get("data") or data
                result = _result[0] if isinstance(_result, list) else _result
                return result
            except Exception as e:
                msg = str(e).lower()
                if "provider_model" in msg and "provider_model" in attempt:
                    logger.warning("provider_model column missing, retrying without it: %s", e)
                    continue
                raise
        return clean
