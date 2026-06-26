from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = SubjectService()
    return await service.list_subjects(current_user["id"])


@router.post("", response_model=SubjectResponse)
async def create_subject(
    body: SubjectCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = SubjectService()
    return await service.create_subject(
        current_user["id"], body.model_dump(exclude_none=True)
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = SubjectService()
    return await service.get_subject(subject_id, current_user["id"])


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: str,
    body: SubjectUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = SubjectService()
    return await service.update_subject(
        subject_id, current_user["id"], body.model_dump(exclude_none=True)
    )


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = SubjectService()
    await service.delete_subject(subject_id, current_user["id"])
    return {"message": "Subject deleted successfully"}
