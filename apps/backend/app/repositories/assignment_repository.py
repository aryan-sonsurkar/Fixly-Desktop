from datetime import datetime, timedelta, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class AssignmentRepository:
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
            else:
                query = query.eq(key, value)
        return query

    async def count(self, user_id: str, filters: dict[str, Any] | None = None) -> int:
        client = get_supabase()
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
        client = get_supabase()
        query = client.table("assignments").select("*")
        query = self._apply_filters(query, {"user_id": user_id, **(filters or {})})

        total_query = client.table("assignments").select("id", count="exact")  # type: ignore[arg-type]
        total_query = total_query.eq("user_id", user_id)
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
        client = get_supabase()
        try:
            response = (
                client.table("assignments")
                .select("*, subjects(name, color)")
                .eq("id", assignment_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
            return data.get("data") or data
        except Exception:
            return None

    async def create_assignment(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        data = {"user_id": user_id, **payload}
        response = client.table("assignments").insert(data).execute()
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = result.get("data") or result
        return _result[0] if isinstance(_result, list) else _result

    async def update_assignment(
        self, assignment_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        client = get_supabase()
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
        client = get_supabase()
        client.table("assignments").delete().eq("id", assignment_id).eq("user_id", user_id).execute()

    async def bulk_update(
        self, ids: list[str], user_id: str, updates: dict[str, Any]
    ) -> list[dict[str, Any]]:
        client = get_supabase()
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
        client = get_supabase()
        result = client.table("assignments").delete().in_("id", ids).eq("user_id", user_id).execute()
        data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        return len(data.get("data", []))

    async def get_attachments(self, assignment_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("attachments")
            .select("*")
            .eq("assignment_id", assignment_id)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def create_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = client.table("attachments").insert(payload).execute()
        result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        _result = result.get("data") or result
        return _result[0] if isinstance(_result, list) else _result

    async def delete_attachment(self, attachment_id: str, user_id: str) -> None:
        client = get_supabase()
        client.table("attachments").delete().eq("id", attachment_id).eq("user_id", user_id).execute()

    async def get_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = client.table("attachments").select("*").eq("id", attachment_id).single().execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def mark_overdue_assignments(self, user_id: str | None = None) -> int:
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        query = (
            client.table("assignments")
            .update({"status": "overdue"})
            .lt("due_date", now)
            .in_("status", ["pending", "in_progress"])
        )
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return len(data.get("data", []))

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        client = get_supabase()
        now = datetime.now(timezone.utc)

        tbl = client.table("assignments")

        total_resp = tbl.select("id", count="exact").eq("user_id", user_id).execute()  # type: ignore[arg-type]
        total = total_resp.count or 0

        completed_resp = tbl.select("id", count="exact").eq("user_id", user_id).eq("status", "completed").execute()  # type: ignore[arg-type]
        completed = completed_resp.count or 0

        pending_resp = tbl.select("id", count="exact").eq("user_id", user_id).eq("status", "pending").execute()  # type: ignore[arg-type]
        pending = pending_resp.count or 0

        in_progress_resp = tbl.select("id", count="exact").eq("user_id", user_id).eq("status", "in_progress").execute()  # type: ignore[arg-type]
        in_progress = in_progress_resp.count or 0

        overdue_resp = tbl.select("id", count="exact").eq("user_id", user_id).eq("status", "overdue").execute()  # type: ignore[arg-type]
        overdue = overdue_resp.count or 0

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        due_today_resp = (
            client.table("assignments")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .gte("due_date", today_start.isoformat())
            .lte("due_date", today_end.isoformat())
            .execute()
        )
        due_today = due_today_resp.count or 0

        week_end = today_start + timedelta(days=7)
        due_week_resp = (
            client.table("assignments")
            .select("id", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
            .gte("due_date", today_start.isoformat())
            .lte("due_date", week_end.isoformat())
            .execute()
        )
        due_week = due_week_resp.count or 0

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
