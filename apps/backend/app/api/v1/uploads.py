from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.supabase import get_supabase
from app.dependencies.auth import get_current_user
from app.repositories.assignment_repository import AssignmentRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["uploads"])

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip", "application/x-zip-compressed",
}


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    assignment_id: str = Form(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise ValidationError(f"File type '{file.content_type}' is not supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError("File exceeds maximum size of 50MB")

    client = get_supabase()
    storage_path = f"{current_user['id']}/{assignment_id}/{file.filename}"

    try:
        client.storage.from_("attachments").upload(
            storage_path, content, file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        logger.error("Storage upload failed", extra={"error": str(e)})
        raise ValidationError("Failed to upload file to storage")

    repo = AssignmentRepository()
    attachment = await repo.create_attachment({
        "assignment_id": assignment_id,
        "user_id": current_user["id"],
        "file_name": file.filename or "unnamed",
        "file_type": file.content_type,
        "file_size": len(content),
        "storage_path": storage_path,
    })

    return attachment


@router.delete("/{attachment_id}")
async def delete_upload(
    attachment_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    repo = AssignmentRepository()
    attachment = await repo.get_attachment(attachment_id)
    if not attachment:
        raise ValidationError("Attachment not found")

    client = get_supabase()
    try:
        client.storage.from_("attachments").remove([attachment["storage_path"]])
    except Exception as e:
        logger.warning("Storage delete failed", extra={"error": str(e)})

    await repo.delete_attachment(attachment_id, current_user["id"])
    return {"message": "File deleted"}
