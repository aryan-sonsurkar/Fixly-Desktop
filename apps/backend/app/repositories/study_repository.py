from datetime import date, datetime, timedelta, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class StudyRepository:
    async def get_calendar_days(self, user_id: str, year: int) -> list[dict[str, Any]]:
        client = get_supabase()
        start = date(year, 1, 1).isoformat()
        end = date(year, 12, 31).isoformat()
        response = (
            client.table("study_days")
            .select("date, study_points, total_study_minutes, mood, productivity_rating")
            .eq("user_id", user_id)
            .gte("date", start)
            .lte("date", end)
            .order("date")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_day(self, user_id: str, day_date: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("study_days")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", day_date)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def upsert_day(self, user_id: str, day_date: str, updates: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        existing = await self.get_day(user_id, day_date)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            updates["updated_at"] = now
            response = (
                client.table("study_days")
                .update(updates)
                .eq("user_id", user_id)
                .eq("date", day_date)
                .single()  # type: ignore[attr-defined]
                .execute()
            )
        else:
            payload = {"user_id": user_id, "date": day_date, **updates, "created_at": now, "updated_at": now}
            response = client.table("study_days").insert(payload).single().execute()  # type: ignore[attr-defined]
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def create_session(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        response = client.table("study_sessions").insert(payload).single().execute()  # type: ignore[attr-defined]
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def get_sessions_for_date(self, user_id: str, session_date: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("study_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("session_date", session_date)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_streak_data(self, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("study_days")
            .select("date, study_points")
            .eq("user_id", user_id)
            .gt("study_points", 0)
            .order("date", desc=True)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_statistics(self, user_id: str) -> dict[str, Any]:
        client = get_supabase()

        tbl = client.table("study_days")
        total_resp = tbl.select("study_points, total_study_minutes").eq("user_id", user_id).execute()
        total_data = total_resp.model_dump() if hasattr(total_resp, "model_dump") else dict(total_resp)
        days = cast(list[dict[str, Any]], total_data.get("data", []))

        total_points = sum(d.get("study_points", 0) for d in days)
        total_minutes = sum(d.get("total_study_minutes", 0) for d in days)
        total_study_days = len(days)
        avg_daily = round(total_minutes / total_study_days, 1) if total_study_days > 0 else 0

        stbl = client.table("study_sessions")
        sessions_resp = stbl.select("activity_type, points, duration_minutes").eq("user_id", user_id).execute()
        sessions_data = sessions_resp.model_dump() if hasattr(sessions_resp, "model_dump") else dict(sessions_resp)
        sessions = cast(list[dict[str, Any]], sessions_data.get("data", []))

        assignments_finished = sum(1 for s in sessions if s.get("activity_type") == "assignment")
        pomodoros_completed = sum(1 for s in sessions if s.get("activity_type") == "pomodoro")

        now = datetime.now(timezone.utc)
        week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")

        weekly = [d for d in days if d.get("date", "") >= week_ago]
        monthly = [d for d in days if d.get("date", "") >= month_ago]

        weekly_trend = [{"date": d["date"], "points": d.get("study_points", 0)} for d in weekly]
        monthly_trend = [{"date": d["date"], "points": d.get("study_points", 0)} for d in monthly]

        return {
            "total_study_points": total_points,
            "total_study_hours": round(total_minutes / 60, 1),
            "average_daily_study_minutes": avg_daily,
            "assignments_finished": assignments_finished,
            "pomodoros_completed": pomodoros_completed,
            "weekly_trend": weekly_trend,
            "monthly_trend": monthly_trend,
            "total_study_days": total_study_days,
        }

    async def get_note(self, user_id: str, note_date: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("study_notes")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", note_date)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def upsert_note(self, user_id: str, note_date: str, content: str) -> dict[str, Any]:
        client = get_supabase()
        existing = await self.get_note(user_id, note_date)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            response = (
                client.table("study_notes")
                .update({"content": content, "updated_at": now})
                .eq("user_id", user_id)
                .eq("date", note_date)
                .single()  # type: ignore[attr-defined]
                .execute()
            )
        else:
            payload = {
                "user_id": user_id,
                "date": note_date,
                "content": content,
                "created_at": now,
                "updated_at": now,
            }
            response = client.table("study_notes").insert(payload).single().execute()  # type: ignore[attr-defined]
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def get_subject_names(self, user_id: str, subject_ids: list[str]) -> dict[str, str]:
        if not subject_ids:
            return {}
        client = get_supabase()
        response = client.table("subjects").select("id, name").eq("user_id", user_id).in_("id", subject_ids).execute()
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        rows = cast(list[dict[str, Any]], data.get("data", []))
        return {r["id"]: r["name"] for r in rows}
