from typing import Any

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    education_type: str | None = None
    education_year: str | None = None
    college_name: str | None = None
    university_board: str | None = None
    branch_stream: str | None = None
    division: str | None = None
    roll_number: str | None = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    education_type: str | None = None
    education_year: str | None = None
    college_name: str | None = None
    university_board: str | None = None
    branch_stream: str | None = None
    division: str | None = None
    roll_number: str | None = None
    xp: int = 0
    streak: int = 0
    onboarding_completed: bool = False


class SettingsUpdate(BaseModel):
    theme: str | None = None
    daily_goal_hours: int | None = Field(default=None, ge=0, le=24)
    pomodoro_focus: int | None = Field(default=None, ge=1, le=120)
    pomodoro_break: int | None = Field(default=None, ge=1, le=60)
    notification_enabled: bool | None = None
    assignment_reminders: bool | None = None
    daily_briefing: bool | None = None
    email_monitoring: bool | None = None
    email_sync_enabled: bool | None = None


class SettingsResponse(BaseModel):
    id: str
    theme: str = "dark"
    daily_goal_hours: int = 0
    pomodoro_focus: int = 25
    pomodoro_break: int = 5
    notification_enabled: bool = True
    assignment_reminders: bool = True
    daily_briefing: bool = True
    email_monitoring: bool = False
    email_sync_enabled: bool = False


class OnboardingRequest(BaseModel):
    profile: ProfileUpdate
    settings: SettingsUpdate
    subjects: list[dict[str, Any]] = []
