from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.email import (
    EmailAccountConnect,
    EmailAccountResponse,
    EmailAccountUpdate,
    EmailAssignmentResponse,
    EmailBriefingResponse,
    EmailMessageResponse,
    EmailReviewAction,
    EmailSyncResponse,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/email", tags=["email"])


# ── Accounts ──────────────────────────────────────────────

@router.post("/accounts/connect", response_model=EmailAccountResponse)
async def connect_account(
    body: EmailAccountConnect,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.connect_account(current_user.id, body.model_dump())


@router.get("/accounts", response_model=list[EmailAccountResponse])
async def list_accounts(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = EmailService(access_token=current_user.access_token)
    return await service.get_accounts(current_user.id)


@router.put("/accounts/{account_id}", response_model=EmailAccountResponse)
async def update_account(
    account_id: UUID,
    body: EmailAccountUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.update_account(
        str(account_id), current_user.id, body.model_dump(exclude_none=True)
    )


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    service = EmailService(access_token=current_user.access_token)
    await service.delete_account(str(account_id), current_user.id)
    return {"message": "Account disconnected"}


# ── Sync ──────────────────────────────────────────────────

@router.post("/accounts/{account_id}/sync", response_model=EmailSyncResponse)
async def sync_account(
    account_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.sync_account(str(account_id), current_user.id)


# ── Messages ──────────────────────────────────────────────

@router.get("/messages")
async def list_messages(
    account_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    unread_only: bool = False,
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.get_messages(
        current_user.id,
        account_id=str(account_id) if account_id else None,
        limit=page_size,
        offset=(page - 1) * page_size,
        unread_only=unread_only,
        search=search,
    )


@router.get("/messages/{message_id}", response_model=EmailMessageResponse)
async def get_message(
    message_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.get_message(str(message_id), current_user.id)


@router.put("/messages/{message_id}/read", response_model=EmailMessageResponse)
async def mark_read(
    message_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.mark_read(str(message_id), current_user.id)


# ── Review Queue ──────────────────────────────────────────

@router.get("/review-queue", response_model=list[EmailAssignmentResponse])
async def get_review_queue(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = EmailService(access_token=current_user.access_token)
    return await service.get_review_queue(current_user.id)


@router.put("/review-queue/{assignment_id}", response_model=EmailAssignmentResponse)
async def review_assignment(
    assignment_id: UUID,
    body: EmailReviewAction,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.review_assignment(
        str(assignment_id), current_user.id, body.status, body.edits
    )


# ── Daily Briefing ────────────────────────────────────────

@router.post("/briefing", response_model=EmailBriefingResponse)
async def generate_briefing(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.generate_briefing(current_user.id)


# ── Unread Count ──────────────────────────────────────────

@router.get("/unread-count")
async def get_unread_count(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, int]:
    service = EmailService(access_token=current_user.access_token)
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}

# ── Dashboard ─────────────────────────────────────────────

@router.get("/dashboard")
async def get_email_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    service = EmailService(access_token=current_user.access_token)
    return await service.get_dashboard_stats(current_user.id)
