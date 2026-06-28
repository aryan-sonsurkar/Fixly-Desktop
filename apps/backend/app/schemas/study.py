from typing import Any

from pydantic import BaseModel, Field

ACTIVITY_PATTERN = (
    r"^(pomodoro|assignment|ai_study|reading|manual|"
    r"email|ocr|pdf_analysis|quiz|flashcard|revision)$"
)


class PointsConfig(BaseModel):
    activity_type: str
    points: int
    description: str | None = None
    is_active: bool = True


class StudySessionCreate(BaseModel):
    activity_type: str = Field(pattern=ACTIVITY_PATTERN)
    duration_minutes: int = Field(default=0, ge=0)
    subject_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StudyDayUpdate(BaseModel):
    mood: str | None = Field(default=None, pattern=r"^(great|good|okay|bad|terrible)?$")
    productivity_rating: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class StudyNoteUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class CalendarDay(BaseModel):
    date: str
    study_points: int = 0
    total_study_minutes: int = 0
    mood: str | None = None
    productivity_rating: int | None = None
    has_notes: bool = False


class CalendarResponse(BaseModel):
    year: int
    days: list[CalendarDay]


class DayDetail(BaseModel):
    date: str
    total_study_minutes: int = 0
    pomodoro_sessions: int = 0
    assignments_completed: int = 0
    subjects_studied: list[str] = []
    ai_conversations: int = 0
    study_points: int = 0
    mood: str | None = None
    productivity_rating: int | None = None
    notes: str | None = None


class StudyStreak(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0


class StudyStatistics(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0
    total_study_points: int = 0
    total_study_hours: float = 0
    average_daily_study_minutes: float = 0
    assignments_finished: int = 0
    pomodoros_completed: int = 0
    weekly_trend: list[dict[str, Any]] = []
    monthly_trend: list[dict[str, Any]] = []
    top_subjects: list[dict[str, Any]] = []
    total_study_days: int = 0
