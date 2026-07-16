from typing import Any

from pydantic import BaseModel, Field


class PomodoroSettings(BaseModel):
    focus_duration: int = Field(default=25, ge=1, le=120)
    short_break_duration: int = Field(default=5, ge=1, le=30)
    long_break_duration: int = Field(default=15, ge=1, le=60)
    long_break_interval: int = Field(default=4, ge=1, le=10)
    daily_goal: int = Field(default=8, ge=1, le=50)
    auto_start_breaks: bool = False
    auto_start_focus: bool = False
    sound_enabled: bool = True
    ticking_sound: bool = False
    desktop_notifications: bool = True


class PomodoroSessionCreate(BaseModel):
    focus_duration: int = Field(default=25, ge=1, le=120)
    break_duration: int = Field(default=5, ge=1, le=30)
    cycles_completed: int = Field(default=1, ge=0)
    total_focus_minutes: int = Field(default=25, ge=0)
    interruptions: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    mood_after: str | None = Field(
        default=None, pattern=r"^(great|good|okay|bad|terrible)$"
    )
    subject_id: str | None = None


class PomodoroSessionResponse(BaseModel):
    id: str
    user_id: str
    focus_duration: int
    break_duration: int
    cycles_completed: int
    total_focus_minutes: int
    interruptions: int
    tags: list[str]
    notes: str | None
    mood_after: str | None
    subject_id: str | None
    daily_goal_progress: float
    date: str
    created_at: str


class PomodoroAnalytics(BaseModel):
    total_sessions: int = 0
    total_focus_minutes: int = 0
    total_cycles: int = 0
    average_focus_minutes: float = 0
    current_streak: int = 0
    longest_streak: int = 0
    daily_goal_progress: float = 0
    weekly_data: list[dict[str, Any]] = []
    monthly_data: list[dict[str, Any]] = []
