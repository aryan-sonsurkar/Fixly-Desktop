from datetime import datetime, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class AIRepository:
    async def create_conversation(self, user_id: str, title: str = "New conversation") -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("conversations")
            .insert({"user_id": user_id, "title": title})
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("conversations")
            .select("id, title, created_at, updated_at, is_pinned, is_archived")
            .eq("user_id", user_id)
            .order("is_pinned", ascending=False)  # type: ignore[call-arg]
            .order("updated_at", ascending=False)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        convs = cast(list[dict[str, Any]], data.get("data", []))

        for conv in convs:
            msg_count = await self.get_message_count(conv["id"])
            conv["message_count"] = msg_count

        return convs

    async def search_conversations(self, user_id: str, query: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("conversations")
            .select("id, title, created_at, updated_at, is_pinned, is_archived")
            .eq("user_id", user_id)
            .ilike("title", f"%{query}%")
            .order("updated_at", ascending=False)  # type: ignore[call-arg]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        convs = cast(list[dict[str, Any]], data.get("data", []))
        for conv in convs:
            msg_count = await self.get_message_count(conv["id"])
            conv["message_count"] = msg_count
        return convs

    async def get_conversation(self, conversation_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return raw.get("data") or (raw if isinstance(raw, dict) and raw.get("id") else None)

    async def update_conversation(self, conversation_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("conversations")
            .update(updates)
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def create_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        provider: str | None = None,
        tokens: int | None = None,
    ) -> dict[str, Any]:
        client = get_supabase()
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
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        result = data.get("data") or data

        client.table("conversations").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq(
            "id", conversation_id
        ).execute()

        return result

    async def get_message_count(self, conversation_id: str) -> int:
        client = get_supabase()
        response = (
            client.table("messages")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("conversation_id", conversation_id)
            .execute()
        )
        return response.count or 0

    async def update_message(
        self, message_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("messages")
            .update(updates)
            .eq("id", message_id)
            .eq("user_id", user_id)
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def delete_message(self, message_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("messages").delete().eq("id", message_id).eq("user_id", user_id).execute()

    async def get_ai_settings(self, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        from app.config import settings

        has_gemini = bool(settings.gemini_api_key)
        has_ollama = bool(settings.ollama_host)

        columns = (
            "preferred_provider, temperature, max_tokens, streaming_enabled, "
            "system_prompt, academic_context, conversation_memory, fallback_provider, ai_enabled"
        )
        response = (
            client.table("settings")
            .select(columns)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        result = data.get("data")
        if isinstance(result, dict) and result.get("preferred_provider"):
            result["ollama_available"] = has_ollama
            result["gemini_available"] = has_gemini
            return result
        return {
            "preferred_provider": "auto",
            "temperature": 0.7,
            "max_tokens": 2048,
            "streaming_enabled": True,
            "system_prompt": None,
            "academic_context": True,
            "conversation_memory": 50,
            "fallback_provider": "auto",
            "ai_enabled": True,
            "ollama_available": has_ollama,
            "gemini_available": has_gemini,
        }

    async def update_ai_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        payload = {"user_id": user_id, **updates}
        response = (
            client.table("settings")
            .upsert(payload, on_conflict="user_id")
            .single()  # type: ignore[attr-defined]
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        result = data.get("data") or data
        return result
