from datetime import date, datetime, timedelta, timezone
from typing import Any, cast

from app.core.logging import get_logger
from app.core.supabase import get_supabase

logger = get_logger(__name__)


class PomodoroRepository:
    async def get_settings(self, user_id: str) -> dict[str, Any] | None:
        client = get_supabase()
        response = (
            client.table("pomodoro_settings")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        result: dict[str, Any] = {}
        if response is not None:
            result = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return result.get("data")

    async def upsert_settings(self, user_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        existing = await self.get_settings(user_id)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            settings["updated_at"] = now
            response = (
                client.table("pomodoro_settings")
                .update(settings)
                .eq("user_id", user_id)
                .single()  # type: ignore[attr-defined]
                .execute()
            )
        else:
            payload = {"user_id": user_id, **settings, "created_at": now, "updated_at": now}
            response = client.table("pomodoro_settings").insert(payload).single().execute()  # type: ignore[attr-defined]
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def create_session(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        daily_goal = await self._get_daily_goal(user_id)
        today = date.today().isoformat()
        today_sessions = await self.get_sessions_for_date(user_id, today)
        total_cycles_today = sum(s.get("cycles_completed", 0) for s in today_sessions)
        progress = min(total_cycles_today / daily_goal, 1.0) if daily_goal > 0 else 0

        payload["daily_goal_progress"] = round(progress, 2)
        payload["date"] = today

        response = client.table("pomodoro_sessions").insert(payload).single().execute()  # type: ignore[attr-defined]
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return data.get("data") or data

    async def get_sessions_for_date(self, user_id: str, session_date: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("pomodoro_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", session_date)
            .order("created_at")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_sessions_range(
        self, user_id: str, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("pomodoro_sessions")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", start_date)
            .lte("date", end_date)
            .order("date")
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def get_streak_data(self, user_id: str) -> list[dict[str, Any]]:
        client = get_supabase()
        response = (
            client.table("pomodoro_sessions")
            .select("date")
            .eq("user_id", user_id)
            .gt("cycles_completed", 0)
            .order("date", desc=True)
            .execute()
        )
        data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return cast(list[dict[str, Any]], data.get("data", []))

    async def _get_daily_goal(self, user_id: str) -> int:
        settings = await self.get_settings(user_id)
        if settings:
            return cast(int, settings.get("daily_goal", 8))
        return 8

    async def get_analytics(self, user_id: str) -> dict[str, Any]:
        all_sessions = await self.get_sessions_range(user_id, "2000-01-01", "2099-12-31")

        total_sessions = len(all_sessions)
        total_focus_minutes = sum(s.get("total_focus_minutes", 0) for s in all_sessions)
        total_cycles = sum(s.get("cycles_completed", 0) for s in all_sessions)
        average_focus = round(total_focus_minutes / total_sessions, 1) if total_sessions > 0 else 0

        active_dates = sorted({s["date"] for s in all_sessions if s.get("cycles_completed", 0) > 0}, reverse=True)

        current_streak = 0
        if active_dates:
            today = date.today().isoformat()
            check = today
            while check in active_dates:
                current_streak += 1
                parsed = date.fromisoformat(check)
                parsed -= timedelta(days=1)
                check = parsed.isoformat()

        longest_streak = 0
        if active_dates:
            sorted_dates = sorted(active_dates)
            temp = 1
            for i in range(1, len(sorted_dates)):
                prev = date.fromisoformat(sorted_dates[i - 1])
                curr = date.fromisoformat(sorted_dates[i])
                if (curr - prev).days == 1:
                    temp += 1
                else:
                    longest_streak = max(longest_streak, temp)
                    temp = 1
            longest_streak = max(longest_streak, temp)

        now = datetime.now(timezone.utc)
        week_ago = (now - timedelta(days=7)).isoformat()[:10]
        month_ago = (now - timedelta(days=30)).isoformat()[:10]

        daily_map: dict[str, int] = {}
        for s in all_sessions:
            d = s["date"]
            daily_map[d] = daily_map.get(d, 0) + s.get("total_focus_minutes", 0)

        weekly_data = [{"date": d, "minutes": m} for d, m in sorted(daily_map.items()) if d >= week_ago]
        monthly_data = [{"date": d, "minutes": m} for d, m in sorted(daily_map.items()) if d >= month_ago]

        daily_goal = await self._get_daily_goal(user_id)
        today = date.today().isoformat()
        today_sessions = [s for s in all_sessions if s["date"] == today]
        today_cycles = sum(s.get("cycles_completed", 0) for s in today_sessions)
        daily_goal_progress = min(today_cycles / daily_goal, 1.0) if daily_goal > 0 else 0

        return {
            "total_sessions": total_sessions,
            "total_focus_minutes": total_focus_minutes,
            "total_cycles": total_cycles,
            "average_focus_minutes": average_focus,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "daily_goal_progress": round(daily_goal_progress, 2),
            "weekly_data": weekly_data,
            "monthly_data": monthly_data,
        }
