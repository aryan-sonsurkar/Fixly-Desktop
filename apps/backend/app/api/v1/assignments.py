from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentsQuery,
    AssignmentStats,
    AssignmentUpdate,
    BulkActionRequest,
    PaginatedAssignments,
)
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=PaginatedAssignments)
async def list_assignments(
    q: AssignmentsQuery = Depends(),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    params = q.model_dump(exclude_none=True)
    return await service.list_assignments(current_user["id"], params)


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    body: AssignmentCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    return await service.create_assignment(
        current_user["id"], body.model_dump(exclude_none=True, mode="json")
    )


@router.get("/stats", response_model=AssignmentStats)
async def get_assignment_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    return await service.get_stats(current_user["id"])


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    return await service.get_assignment(assignment_id, current_user["id"])


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    return await service.update_assignment(
        assignment_id, current_user["id"], body.model_dump(exclude_none=True)
    )


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = AssignmentService()
    await service.delete_assignment(assignment_id, current_user["id"])
    return {"message": "Assignment deleted"}


@router.post("/{assignment_id}/duplicate", response_model=AssignmentResponse)
async def duplicate_assignment(
    assignment_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    return await service.duplicate_assignment(assignment_id, current_user["id"])


@router.post("/bulk")
async def bulk_action(
    body: BulkActionRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = AssignmentService()
    result, affected = await service.bulk_action(body.ids, current_user["id"], body.action, body.value)
    return {"affected": affected, "data": result}


@router.get("/{assignment_id}/attachments")
async def get_assignment_attachments(
    assignment_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = AssignmentService()
    return await service.get_attachments(assignment_id, current_user["id"])
