from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

import html
import re

from fastapi import Request

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.rate_limiter import upload_limiter
from app.core.supabase import get_supabase_for_user
from app.dependencies.auth import CurrentUser, get_current_user
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
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip"}
# Magic bytes mapping (first bytes)
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"\x89PNG": "image/png",
    b"\xFF\xD8\xFF": "image/jpeg",
    b"GIF8": "image/gif",
    b"RIFF": "image/webp",  # webp is RIFF....WEBP
    b"PK\x03\x04": "application/zip",  # zip/docx/xlsx/pptx are zip
}


def _validate_magic_bytes(content: bytes, claimed_type: str) -> bool:
    if not content:
        return False
    for magic, mime in MAGIC_BYTES.items():
        if content.startswith(magic):
            # zip-based formats share PK header, allow docx/xlsx/pptx/zip interchangeably
            if magic == b"PK\x03\x04":
                return claimed_type in {
                    "application/zip", "application/x-zip-compressed",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                }
            return mime == claimed_type
    # For msword (OLE) starts with D0 CF 11 E0
    if content.startswith(b"\xD0\xCF\x11\xE0") and claimed_type == "application/msword":
        return True
    return False


def _sanitize_filename(name: str) -> str:
    # Block path traversal, trim, escape html, limit length
    name = name.strip().replace("\\", "/").split("/")[-1]
    name = html.escape(name)
    # remove null bytes and control chars
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    # block double extensions like .pdf.exe
    if ".." in name or name.count(".") > 2:
        # allow single dot, but block suspicious double ext
        parts = name.split(".")
        if len(parts) > 2 and parts[-1].lower() in {"exe", "sh", "bat", "cmd", "js", "html"}:
            raise ValidationError("Suspicious file extension")
    if len(name) > 255:
        name = name[:255]
    if not name or name in {".", ".."}:
        raise ValidationError("Invalid filename")
    return name


@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    assignment_id: UUID = Form(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    upload_limiter.check(request)
    assignment_id_str = str(assignment_id)
    # Validate MIME + extension + magic bytes (defense in depth)
    claimed = (file.content_type or "").lower()
    if claimed and claimed not in ALLOWED_TYPES:
        raise ValidationError(f"File type '{claimed}' is not supported")
    filename = _sanitize_filename(file.filename or "unnamed")
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File extension '{ext}' is not allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError("File exceeds maximum size of 50MB")
    if len(content) == 0:
        raise ValidationError("Empty file not allowed")
    # Magic byte verification when possible
    if claimed and not _validate_magic_bytes(content[:12], claimed):
        # For webp RIFF check needs WEBP at offset 8
        if not (claimed == "image/webp" and content[:4] == b"RIFF" and content[8:12] == b"WEBP"):
            logger.warning("Magic byte mismatch", extra={"claimed": claimed, "filename": filename})
            raise ValidationError("File content does not match its extension")

    repo = AssignmentRepository(access_token=current_user.access_token)
    assignment = await repo.get_assignment(assignment_id_str, current_user.id)
    if not assignment:
        raise ValidationError("Assignment not found")

    client = get_supabase_for_user(current_user.access_token)
    storage_path = f"{current_user.id}/{assignment_id_str}/{filename}"

    try:
        client.storage.from_("attachments").upload(
            storage_path, content, file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        logger.error("Storage upload failed", extra={"error": str(e)})
        raise ValidationError("Failed to upload file to storage")

    attachment = await repo.create_attachment({
        "assignment_id": assignment_id_str,
        "user_id": current_user.id,
        "file_name": filename,
        "file_type": claimed or file.content_type,
        "file_size": len(content),
        "storage_path": storage_path,
    })

    # Trim response: only return safe fields
    return {
        "id": attachment.get("id"),
        "file_name": attachment.get("file_name"),
        "file_type": attachment.get("file_type"),
        "file_size": attachment.get("file_size"),
        "created_at": attachment.get("created_at"),
    }


@router.delete("/{attachment_id}")
async def delete_upload(
    attachment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = AssignmentRepository(access_token=current_user.access_token)
    attachment_id_str = str(attachment_id)
    attachment = await repo.get_attachment(attachment_id_str, current_user.id)
    if not attachment:
        raise ValidationError("Attachment not found")

    client = get_supabase_for_user(current_user.access_token)
    try:
        client.storage.from_("attachments").remove([attachment["storage_path"]])
    except Exception as e:
        logger.warning("Storage delete failed", extra={"error": str(e)})

    await repo.delete_attachment(attachment_id_str, current_user.id)
    return {"message": "File deleted"}
