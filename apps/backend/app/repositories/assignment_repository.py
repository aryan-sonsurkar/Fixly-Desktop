from datetime import datetime, timedelta, timezone
from typing import Any, cast

from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase, get_supabase_for_user
from app.repositories.utils import single_or_none

logger = get_logger(__name__)


class AssignmentRepository:

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

    def _parse_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in row.items()
        }

    def _apply_filters(self, query: Any, filters: dict[str, Any]) -> Any:
        user_id = filters.get("user_id")
        if user_id:
            query = query.eq("user_id", user_id)

        for key, value in filters.items():
            if key == "user_id" or value is None or value == "":
                continue
            if key == "search":
                query = query.text_search("title", value)
            elif key == "tags":
                if isinstance(value, list) and value:
                    query = query.contains("tags", value)
            elif key == "due_date_from":
                query = query.gte("due_date", value.isoformat() if hasattr(value, "isoformat") else value)
            elif key == "due_date_to":
                query = query.lte("due_date", value.isoformat() if hasattr(value, "isoformat") else value)
            elif isinstance(value, list):
                if value:
                    query = query.in_(key, value)
            else:
                query = query.eq(key, value)
        return query

    async def count(self, user_id: str, filters: dict[str, Any] | None = None) -> int:
        client = self._client
        query = client.table("assignments").select("id", count="exact")  # type: ignore[arg-type]
        query = query.eq("user_id", user_id)
        if filters:
            query = self._apply_filters(query, {**filters})
        response = query.execute()
        return response.count or 0

    async def list_assignments(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        client = self._client
        merged_filters = {"user_id": user_id, **(filters or {})}
        query = client.table("assignments").select("*")
        query = self._apply_filters(query, merged_filters)

        total_query = client.table("assignments").select("id", count="exact")  # type: ignore[arg-type]
        total_query = self._apply_filters(total_query, merged_filters)
        total_response = total_query.execute()
        total = total_response.count or 0

        query = query.order(sort_by, desc=(sort_order != "asc"))
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = cast(list[dict[str, Any]], data.get("data", []))
        return rows, total

    async def get_assignment(self, assignment_id: str, user_id: str) -> dict[str, Any] | None:
        client = self._client
        return single_or_none(
            client.table("assignments")
            .select("*, subjects(name, color)")
            .eq("id", assignment_id)
            .eq("user_id", user_id)
        )

    async def create_assignment(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        data = {"user_id": user_id, **payload}
        response = client.table("assignments").insert(data).execute()
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = result.get("data") or result
        return _result[0] if isinstance(_result, list) else _result

    async def update_assignment(
        self, assignment_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = self._client
        if "status" in updates and updates["status"] == "completed":
            updates["completion_date"] = datetime.now(timezone.utc).isoformat()
        response = (
            client.table("assignments")
            .update(updates)
            .eq("id", assignment_id)
            .eq("user_id", user_id)

            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _data = data.get("data") or data
        return _data[0] if isinstance(_data, list) else _data

    async def delete_assignment(self, assignment_id: str, user_id: str) -> None:
        client = self._client
        client.table("assignments").delete().eq("id", assignment_id).eq("user_id", user_id).execute()

    async def bulk_update(
        self, ids: list[str], user_id: str, updates: dict[str, Any]
    ) -> list[dict[str, Any]]:
        client = self._client
        response = (
            client.table("assignments")
            .update(updates)
            .in_("id", ids)
            .eq("user_id", user_id)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def bulk_delete(self, ids: list[str], user_id: str) -> int:
        client = self._client
        result = client.table("assignments").delete().in_("id", ids).eq("user_id", user_id).execute()
        data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        return len(data.get("data", []))

    async def get_attachments(self, assignment_id: str, user_id: str) -> list[dict[str, Any]]:
        client = self._client
        response = (
            client.table("attachments")
            .select("*")
            .eq("assignment_id", assignment_id)
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def create_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        response = client.table("attachments").insert(payload).execute()
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = result.get("data") or result
        return _result[0] if isinstance(_result, list) else _result

    async def delete_attachment(self, attachment_id: str, user_id: str) -> None:
        client = self._client
        client.table("attachments").delete().eq("id", attachment_id).eq("user_id", user_id).execute()

    async def get_attachment(self, attachment_id: str, user_id: str) -> dict[str, Any] | None:
        client = self._client
        return single_or_none(
            client.table("attachments")
            .select("*")
            .eq("id", attachment_id)
            .eq("user_id", user_id)
        )

    async def mark_overdue_assignments(self, user_id: str) -> int:
        client = self._client
        now = datetime.now(timezone.utc).isoformat()
        query = (
            client.table("assignments")
            .update({"status": "overdue"})
            .lt("due_date", now)
            .in_("status", ["pending", "in_progress"])
        )
        query = query.eq("user_id", user_id)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return len(data.get("data", []))

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        import asyncio

        from app.core.threads import run_in_thread

        client = self._client
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        week_end = today_start + timedelta(days=7)

        def _count(status: str | None = None, due_from: str | None = None, due_to: str | None = None) -> int:
            q = client.table("assignments").select("id", count="exact").eq("user_id", user_id)  # type: ignore[arg-type]
            if status:
                q = q.eq("status", status)
            if due_from:
                q = q.gte("due_date", due_from)
            if due_to:
                q = q.lte("due_date", due_to)
            return q.execute().count or 0

        # Run all 7 counts in parallel via thread pool
        total, completed, pending, in_progress, overdue, due_today, due_week = await asyncio.gather(
            run_in_thread(lambda: _count()),
            run_in_thread(lambda: _count(status="completed")),
            run_in_thread(lambda: _count(status="pending")),
            run_in_thread(lambda: _count(status="in_progress")),
            run_in_thread(lambda: _count(status="overdue")),
            run_in_thread(lambda: _count(due_from=today_start.isoformat(), due_to=today_end.isoformat())),
            run_in_thread(lambda: _count(due_from=today_start.isoformat(), due_to=week_end.isoformat())),
        )

        completion_pct = (completed / total * 100) if total > 0 else 0.0

        avg_time = None
        if completed > 0:
            avg_resp = (
                client.table("assignments")
                .select("created_at, completion_date")
                .eq("user_id", user_id)
                .eq("status", "completed")
                .not_.is_("completion_date", "null")
                .execute()
            )
            avg_data = avg_resp.model_dump() if hasattr(avg_resp, "model_dump") else dict(avg_resp)
            rows = avg_data.get("data", [])
            if rows:
                total_hours = 0.0
                count = 0
                for r in rows:
                    created = r.get("created_at")
                    completed_dt = r.get("completion_date")
                    if created and completed_dt:
                        diff = (
                            datetime.fromisoformat(completed_dt) -
                            datetime.fromisoformat(created)
                        )
                        total_hours += diff.total_seconds() / 3600
                        count += 1
                if count > 0:
                    avg_time = round(total_hours / count, 2)

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "overdue": overdue,
            "completion_percentage": round(completion_pct, 1),
            "due_today": due_today,
            "due_this_week": due_week,
            "avg_completion_time_hours": avg_time,
        }
