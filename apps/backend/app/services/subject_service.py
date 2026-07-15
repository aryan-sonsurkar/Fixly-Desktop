from typing import Any

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.subject_repository import SubjectRepository
from app.schemas.subject import SubjectCreate

logger = get_logger(__name__)


class SubjectService:
    def __init__(self) -> None:
        self.repository = SubjectRepository()

    async def list_subjects(self, user_id: str) -> list[dict[str, Any]]:
        return await self.repository.list_subjects(user_id)

    async def get_subject(self, subject_id: str, user_id: str) -> dict[str, Any]:
        subject = await self.repository.get_subject(subject_id, user_id)
        if not subject:
            raise NotFoundError("Subject not found")
        return subject

    async def create_subject(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self.repository.create_subject(user_id, data)

    async def update_subject(
        self, subject_id: str, user_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        existing = await self.repository.get_subject(subject_id, user_id)
        if not existing:
            raise NotFoundError("Subject not found")
        clean = {k: v for k, v in data.items() if v is not None}
        return await self.repository.update_subject(subject_id, user_id, clean)

    async def delete_subject(self, subject_id: str, user_id: str) -> None:
        existing = await self.repository.get_subject(subject_id, user_id)
        if not existing:
            raise NotFoundError("Subject not found")
        await self.repository.delete_subject(subject_id, user_id)

    async def bulk_create(
        self, user_id: str, subjects: list[SubjectCreate]
    ) -> list[dict[str, Any]]:
        created = []
        for subj in subjects:
            data = subj.model_dump(exclude_none=True)
            data.pop("user_id", None)
            result = await self.repository.create_subject(user_id, data)
            created.append(result)
        return created
