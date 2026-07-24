from datetime import datetime, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class EmailRepository:
    # ── Accounts ──────────────────────────────────────────

    async def create_account(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        payload = {"user_id": user_id, **data}
        response = (
            client.table("email_accounts")
            .insert(payload)

            .execute()
        )
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _raw = raw.get("data") or raw
        return _raw[0] if isinstance(_raw, list) else _raw

    async def get_accounts(self, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("email_accounts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_account(self, account_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("email_accounts")
            .select("*")
            .eq("id", account_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def update_account(self, account_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("email_accounts")
            .update(updates)
            .eq("id", account_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def delete_account(self, account_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("email_accounts").delete().eq("id", account_id).eq("user_id", user_id).execute()

    # ── Messages ──────────────────────────────────────────

    async def upsert_message(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("email_messages")
            .upsert(payload, on_conflict="user_id,message_id")

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_messages(
        self, user_id: str, account_id: str | None = None,
        limit: int = 50, offset: int = 0,
        unread_only: bool = False,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        client = get_supabase()
        query = client.table("email_messages").select("*", count="exact").eq("user_id", user_id)  # type: ignore[arg-type]

        if account_id:
            query = query.eq("account_id", account_id)
        if unread_only:
            query = query.eq("is_read", False)
        if search:
            query = query.or_(f"subject.ilike.%{search}%,from_name.ilike.%{search}%,body_text.ilike.%{search}%")
        query = query.order("received_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        messages = cast(list[dict[str, Any]], data.get("data", []))
        total = response.count or 0

        # Attach classifications and assignments
        if messages:
            msg_ids = [m["id"] for m in messages]
            classifications = await self._get_classifications_bulk(user_id, msg_ids)
            assignments = await self._get_assignments_bulk(user_id, msg_ids)
            for m in messages:
                m["classification"] = classifications.get(m["id"])
                m["assignment"] = assignments.get(m["id"])

        return messages, total

    async def get_messages_light(
        self, user_id: str, limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch messages with only key fields — no classifications attached."""
        client = get_supabase()
        response = (
            client.table("email_messages")
            .select("id,message_id,from_email,subject,account_id")
            .eq("user_id", user_id)
            .order("received_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_message(self, message_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("email_messages")
            .select("*")
            .eq("id", message_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        msg = result.get("data")
        if msg:
            cls = await self.get_classification(msg["id"], user_id)
            asgn = await self.get_assignment(msg["id"], user_id)
            msg["classification"] = cls
            msg["assignment"] = asgn
        return msg

    async def update_message(self, message_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("email_messages")
            .update(updates)
            .eq("id", message_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    # ── Classifications ───────────────────────────────────

    async def create_classification(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("email_classifications")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_classification(self, email_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("email_classifications")
            .select("*")
            .eq("email_id", email_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def _get_classifications_bulk(self, user_id: str, email_ids: list[str]) -> dict[str, Any]:
        if not email_ids:
            return {}
        client = get_supabase()
        response = (
            client.table("email_classifications")
            .select("*")
            .eq("user_id", user_id)
            .in_("email_id", email_ids)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = cast(list[dict[str, Any]], data.get("data", []))
        return {r["email_id"]: r for r in rows}

    # ── Assignments ───────────────────────────────────────

    async def create_assignment(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("email_assignments")
            .insert(payload)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_assignment(self, email_id: str, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("email_assignments")
            .select("*")
            .eq("email_id", email_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def _get_assignments_bulk(self, user_id: str, email_ids: list[str]) -> dict[str, Any]:
        if not email_ids:
            return {}
        client = get_supabase()
        response = (
            client.table("email_assignments")
            .select("*")
            .eq("user_id", user_id)
            .in_("email_id", email_ids)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = cast(list[dict[str, Any]], data.get("data", []))
        return {r["email_id"]: r for r in rows}

    async def update_assignment(self, assignment_id: str, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = (
            client.table("email_assignments")
            .update(updates)
            .eq("id", assignment_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def get_review_queue(
        self, user_id: str, status: str | None = None
    ) -> list[dict[str, Any]]:
        client = get_supabase()
        query = (
            client.table("email_assignments")
            .select("*, email:email_id(*)")
            .eq("user_id", user_id)
            .neq("status", "converted")
        )
        if status:
            query = query.eq("status", status)
        else:
            query = query.in_("status", ["pending", "approved", "edited"])
        query = query.order("created_at", desc=True)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_unread_count(self, user_id: str) -> int:
        client = get_supabase()
        response = (
            client.table("email_messages")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return response.count or 0

    async def get_recent_academic_emails(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("email_messages")
            .select("*, classification:email_id(*)")
            .eq("user_id", user_id)
            .not_.is_("body_text", "null")
            .order("received_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))
