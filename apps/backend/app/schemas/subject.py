from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = None
    icon: str | None = None
    credits: int | None = Field(default=None, ge=0, le=30)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None
    icon: str | None = None
    credits: int | None = Field(default=None, ge=0, le=30)


class SubjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str | None = None
    icon: str | None = None
    credits: int | None = None
    created_at: str
    updated_at: str
