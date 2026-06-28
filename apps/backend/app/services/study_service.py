from datetime import date, timedelta
from typing import Any

from app.core.logging import get_logger
from app.repositories.study_repository import StudyRepository
from app.services.study_scoring import calculate_daily_goal_bonus, get_points

logger = get_logger(__name__)


class StudyService:
    def __init__(self) -> None:
        self.repository = StudyRepository()

    async def get_calendar(self, user_id: str, year: int) -> dict[str, Any]:
        days = await self.repository.get_calendar_days(user_id, year)
        calendar_days = []
        for d in days:
            calendar_days.append({
                "date": d["date"],
                "study_points": d.get("study_points", 0),
                "total_study_minutes": d.get("total_study_minutes", 0),
                "mood": d.get("mood"),
                "productivity_rating": d.get("productivity_rating"),
            })
        return {"year": year, "days": calendar_days}

    async def get_day_detail(self, user_id: str, day_date: str) -> dict[str, Any]:
        day = await self.repository.get_day(user_id, day_date)
        if not day:
            return {
                "date": day_date,
                "total_study_minutes": 0,
                "pomodoro_sessions": 0,
                "assignments_completed": 0,
                "subjects_studied": [],
                "ai_conversations": 0,
                "study_points": 0,
                "mood": None,
                "productivity_rating": None,
                "notes": None,
            }
        sessions = await self.repository.get_sessions_for_date(user_id, day_date)
        subject_ids: list[str] = [s["subject_id"] for s in sessions if s.get("subject_id")]
        subject_names = await self.repository.get_subject_names(user_id, subject_ids) if subject_ids else {}
        subjects_studied = [subject_names.get(s, s) for s in subject_ids]

        note_data = await self.repository.get_note(user_id, day_date)
        notes = note_data.get("content") if note_data else day.get("notes")

        return {
            "date": day_date,
            "total_study_minutes": day.get("total_study_minutes", 0),
            "pomodoro_sessions": day.get("pomodoro_sessions", 0),
            "assignments_completed": day.get("assignments_completed", 0),
            "subjects_studied": subjects_studied,
            "ai_conversations": day.get("ai_conversations", 0),
            "study_points": day.get("study_points", 0),
            "mood": day.get("mood"),
            "productivity_rating": day.get("productivity_rating"),
            "notes": notes,
        }

    async def update_day(self, user_id: str, day_date: str, data: dict[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if "mood" in data:
            updates["mood"] = data["mood"]
        if "productivity_rating" in data:
            updates["productivity_rating"] = data["productivity_rating"]
        if "notes" in data:
            updates["notes"] = data["notes"]

        if updates:
            await self.repository.upsert_day(user_id, day_date, updates)

        if "notes" in data:
            await self.repository.upsert_note(user_id, day_date, data["notes"])

        return await self.get_day_detail(user_id, day_date)

    async def log_session(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        activity_type = data["activity_type"]
        points = get_points(activity_type)
        duration = data.get("duration_minutes", 0)
        session_date = date.today().isoformat()

        session_payload = {
            "user_id": user_id,
            "activity_type": activity_type,
            "points": points,
            "duration_minutes": duration,
            "subject_id": data.get("subject_id"),
            "metadata": data.get("metadata", {}),
            "session_date": session_date,
        }
        session = await self.repository.create_session(user_id, session_payload)

        day = await self.repository.get_day(user_id, session_date)
        day_updates: dict[str, Any] = {}
        base = day if day else {}
        day_updates["study_points"] = base.get("study_points", 0) + points
        day_updates["total_study_minutes"] = base.get("total_study_minutes", 0) + duration
        day_updates["pomodoro_sessions"] = base.get("pomodoro_sessions", 0) + (
            1 if activity_type == "pomodoro" else 0
        )
        day_updates["assignments_completed"] = base.get("assignments_completed", 0) + (
            1 if activity_type == "assignment" else 0
        )
        day_updates["ai_conversations"] = base.get("ai_conversations", 0) + (
            1 if activity_type == "ai_study" else 0
        )

        if data.get("subject_id"):
            existing_subjects = day.get("subjects_studied", []) if day else []
            if data["subject_id"] not in existing_subjects:
                existing_subjects = list(existing_subjects) + [data["subject_id"]]
            day_updates["subjects_studied"] = existing_subjects

        daily_goal_bonus = calculate_daily_goal_bonus(day_updates["study_points"])
        if daily_goal_bonus > 0:
            day_updates["study_points"] += daily_goal_bonus

        await self.repository.upsert_day(user_id, session_date, day_updates)
        return session

    async def get_statistics(self, user_id: str) -> dict[str, Any]:
        stats = await self.repository.get_statistics(user_id)
        streaks = await self._calculate_streaks(user_id)
        return {**stats, **streaks}

    async def get_streak(self, user_id: str) -> dict[str, Any]:
        return await self._calculate_streaks(user_id)

    async def _calculate_streaks(self, user_id: str) -> dict[str, Any]:
        days = await self.repository.get_streak_data(user_id)
        active_dates = sorted({d["date"] for d in days}, reverse=True)

        if not active_dates:
            return {"current_streak": 0, "longest_streak": 0}

        today = date.today().isoformat()
        current_streak = 0
        check_date = today

        while check_date in active_dates:
            current_streak += 1
            parsed = date.fromisoformat(check_date)
            parsed -= timedelta(days=1)
            check_date = parsed.isoformat()

        longest_streak = 0
        temp_streak = 1
        sorted_dates = sorted(active_dates)
        for i in range(1, len(sorted_dates)):
            prev = date.fromisoformat(sorted_dates[i - 1])
            curr = date.fromisoformat(sorted_dates[i])
            if (curr - prev).days == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        longest_streak = max(longest_streak, temp_streak)

        return {"current_streak": current_streak, "longest_streak": longest_streak}
