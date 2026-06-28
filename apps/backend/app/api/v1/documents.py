from typing import Any

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.dependencies.auth import get_current_user
from app.schemas.document import (
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentDetailResponse,
    DocumentFlashcardsRequest,
    DocumentNotesRequest,
    DocumentQuizRequest,
    DocumentRename,
    DocumentResponse,
    DocumentSummaryRequest,
    DocumentUpdate,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/recent", response_model=list[DocumentResponse])
async def get_recent_documents(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    service = DocumentService()
    return await service.get_recent_documents(current_user["id"], limit)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.upload_document(current_user["id"], file)


@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.process_document(document_id, current_user["id"])


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.get_document_detail(document_id, current_user["id"])


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    body: DocumentUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.update_document(
        document_id, current_user["id"], body.model_dump(exclude_none=True)
    )


@router.put("/{document_id}/rename", response_model=DocumentResponse)
async def rename_document(
    document_id: str,
    body: DocumentRename,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.update_document(
        document_id, current_user["id"], {"original_name": body.original_name}
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    service = DocumentService()
    await service.delete_document(document_id, current_user["id"])
    return {"message": "Document deleted"}


@router.post("/chat", response_model=DocumentChatResponse)
async def chat_with_document(
    body: DocumentChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.chat_with_document(
        current_user["id"], body.document_id, body.message, body.conversation_id
    )


@router.post("/{document_id}/summarize")
async def summarize_document(
    document_id: str,
    body: DocumentSummaryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.generate_document_content(
        current_user["id"], document_id, "summarize", max_length=body.max_length
    )


@router.post("/{document_id}/notes")
async def generate_notes(
    document_id: str,
    body: DocumentNotesRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.generate_document_content(
        current_user["id"], document_id, "notes", style=body.style
    )


@router.post("/{document_id}/flashcards")
async def generate_flashcards(
    document_id: str,
    body: DocumentFlashcardsRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.generate_document_content(
        current_user["id"], document_id, "flashcards", count=body.count
    )


@router.post("/{document_id}/quiz")
async def generate_quiz(
    document_id: str,
    body: DocumentQuizRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.generate_document_content(
        current_user["id"], document_id, "quiz",
        count=body.count, difficulty=body.difficulty,
    )


@router.get("")
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    subject_id: str | None = None,
    status: str | None = None,
    file_type: str | None = None,
    search: str | None = None,
    favorites_only: bool = False,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    service = DocumentService()
    return await service.list_documents(current_user["id"], {
        "page": page,
        "page_size": page_size,
        "subject_id": subject_id,
        "status": status,
        "file_type": file_type,
        "search": search,
        "favorites_only": favorites_only,
    })



