import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.ai_repository import AIRepository
from app.repositories.document_repository import DocumentRepository
from app.services.ai_service import AIService
from app.services.context_service import ContextService
from app.services.ocr_service import OCRService
from app.services.pdf_service import PDFService
from app.services.study_service import StudyService

logger = get_logger(__name__)

ALLOWED_TYPES = {"pdf", "png", "jpg", "jpeg", "webp"}
IMAGE_TYPES = {"png", "jpg", "jpeg", "webp"}

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "uploads",
    "documents",
)


class DocumentService:
    def __init__(self) -> None:
        self.repository = DocumentRepository()
        self.ai_repo = AIRepository()
        self.pdf_service = PDFService()
        self.ocr_service = OCRService()
        self.context_service = ContextService()
        self.ai_service = AIService()
        self.study_service = StudyService()
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    async def upload_document(self, user_id: str, file: Any) -> dict[str, Any]:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_TYPES:
            raise ValidationError(f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_TYPES))}")

        content = await file.read()
        file_id = str(uuid.uuid4())
        storage_name = f"{file_id}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, storage_name)

        with open(file_path, "wb") as f:
            f.write(content)

        doc = await self.repository.create_document(user_id, {
            "user_id": user_id,
            "filename": storage_name,
            "original_name": file.filename,
            "file_type": ext,
            "file_size": len(content),
            "status": "pending",
            "storage_path": file_path,
        })

        logger.info("Uploaded document %s for user %s: %s", doc["id"], user_id, file.filename)
        return doc

    async def process_document(self, document_id: str, user_id: str) -> dict[str, Any]:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise NotFoundError("Document not found")

        file_path = doc.get("storage_path")
        file_type = doc.get("file_type", "")
        if not file_path or not os.path.exists(file_path):
            raise NotFoundError("File not found on disk")

        await self.repository.update_document(document_id, user_id, {"status": "processing"})

        try:
            if file_type == "pdf":
                result = await self.pdf_service.process_pdf(document_id, user_id, file_path)
            elif file_type in IMAGE_TYPES:
                ocr_result = await self.ocr_service.process_image(
                    document_id, user_id, file_path, file_type
                )
                text = ocr_result.get("extracted_text", "")
                chunks = await self.pdf_service.chunk_text(text)
                for chunk in chunks:
                    chunk["document_id"] = document_id
                    chunk["user_id"] = user_id
                if chunks:
                    await self.repository.create_chunks(chunks)
                result = {
                    "document_id": document_id,
                    "chunk_count": len(chunks),
                    "processing_time_ms": ocr_result.get("processing_time_ms", 0),
                }
            else:
                raise ValueError(f"Unsupported file type for processing: {file_type}")

            await self.repository.update_document(document_id, user_id, {
                "status": "processed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

            try:
                await self.study_service.log_session(user_id, {
                    "activity_type": "pdf_analysis" if file_type == "pdf" else "ocr",
                    "duration_minutes": max(1, result.get("processing_time_ms", 0) // 60000),
                    "subject_id": doc.get("subject_id"),
                    "metadata": {
                        "document_id": document_id,
                        "document_name": doc.get("original_name"),
                        "file_type": file_type,
                    },
                })
            except Exception as e:
                logger.error("Failed to log study session for document: %s", e)

            return result

        except Exception as e:
            logger.error("Document processing failed: %s", e)
            await self.repository.update_document(document_id, user_id, {
                "status": "failed",
                "error_message": str(e),
            })
            raise

    async def chat_with_document(
        self, user_id: str, document_id: str, message: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise ValidationError("Document not found")

        if not conversation_id:
            conv = await self.ai_repo.create_conversation(
                user_id, f"Document: {doc.get('original_name', 'Untitled')}"
            )
            conversation_id = conv["id"]
            await self.repository.link_conversation(document_id, conversation_id, user_id)

        context = await self.context_service.build_context_prompt(
            document_id, user_id, message
        )

        enriched_message = (
            f"I'm analyzing the document '{doc.get('original_name', 'Untitled')}' "
            f"({doc.get('file_type', 'unknown')}).\n\n"
            f"Here is the relevant content from the document:\n\n{context}\n\n"
            f"User question: {message}"
        )

        result = await self.ai_service.chat(
            user_id, enriched_message, conversation_id, stream=False
        )

        chunks_used = await self.context_service.get_relevant_chunks(
            document_id, user_id, message
        )

        try:
            await self.study_service.log_session(user_id, {
                "activity_type": "ai_study",
                "duration_minutes": 1,
                "subject_id": doc.get("subject_id"),
                "metadata": {
                    "document_id": document_id,
                    "document_name": doc.get("original_name"),
                    "conversation_id": conversation_id,
                },
            })
        except Exception as e:
            logger.error("Failed to log AI study session: %s", e)

        return {
            "message": result["message"],
            "conversation": result["conversation"],
            "chunks_used": chunks_used,
        }

    async def generate_document_content(
        self, user_id: str, document_id: str, prompt_type: str, **kwargs: Any
    ) -> dict[str, Any]:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise ValidationError("Document not found")

        all_chunks = await self.repository.get_chunks(document_id, user_id)
        full_text = "\n\n".join(c.get("content", "") for c in all_chunks)
        name = doc.get("original_name", "Document")

        prompts = {
            "summarize": (
                f"Summarize the following document '{name}' in a clear, structured way. "
                f"Extract key points, main arguments, and important details. "
                f"Keep the summary to approximately {kwargs.get('max_length', 500)} words.\n\n"
                f"Document content:\n{full_text[:10000]}"
            ),
            "notes": (
                f"Generate {kwargs.get('style', 'detailed')} study notes from the document '{name}'. "
                f"Organize by topics and key concepts. Use bullet points and headings.\n\n"
                f"Document content:\n{full_text[:10000]}"
            ),
            "flashcards": (
                f"Create {kwargs.get('count', 10)} flashcards from the document '{name}'. "
                f"Format each as Q&A pairs. Cover the most important concepts.\n\n"
                f"Document content:\n{full_text[:10000]}"
            ),
            "quiz": (
                f"Create {kwargs.get('count', 5)} {kwargs.get('difficulty', 'medium')}-difficulty "
                f"quiz questions from the document '{name}'. Include multiple choice and short answer. "
                f"Provide the correct answers after each question.\n\n"
                f"Document content:\n{full_text[:10000]}"
            ),
            "explain": (
                f"Explain the difficult concepts in the document '{name}' in simple terms. "
                f"Break down complex ideas for a student.\n\n"
                f"Document content:\n{full_text[:10000]}"
            ),
        }

        prompt = prompts.get(prompt_type)
        if not prompt:
            raise ValueError(f"Unknown content type: {prompt_type}")

        conv = await self.ai_repo.create_conversation(user_id, f"{prompt_type.title()} from {name}")
        await self.repository.link_conversation(document_id, conv["id"], user_id)

        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        points_map = {
            "summarize": "pdf_analysis",
            "notes": "revision",
            "flashcards": "flashcard",
            "quiz": "quiz",
            "explain": "ai_study",
        }

        try:
            await self.study_service.log_session(user_id, {
                "activity_type": points_map.get(prompt_type, "ai_study"),
                "duration_minutes": 2,
                "subject_id": doc.get("subject_id"),
                "metadata": {
                    "document_id": document_id,
                    "document_name": name,
                    "content_type": prompt_type,
                },
            })
        except Exception as e:
            logger.error("Failed to log content generation session: %s", e)

        return {
            "message": result["message"],
            "conversation": result["conversation"],
        }

    async def get_document_detail(self, document_id: str, user_id: str) -> dict[str, Any]:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise ValidationError("Document not found")

        chunks = await self.repository.get_chunks(document_id, user_id)
        conv_ids = await self.repository.get_conversation_ids(document_id, user_id)

        await self.repository.update_document(document_id, user_id, {
            "last_opened_at": datetime.now(timezone.utc).isoformat(),
        })

        return {**doc, "chunks": chunks, "conversation_ids": conv_ids}

    async def list_documents(
        self, user_id: str, filters: dict[str, Any]
    ) -> dict[str, Any]:
        docs, total = await self.repository.list_documents(user_id, **filters)
        return {
            "documents": docs,
            "total": total,
            "page": filters.get("page", 1),
            "page_size": filters.get("page_size", 20),
        }

    async def update_document(
        self, document_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise ValidationError("Document not found")
        return await self.repository.update_document(document_id, user_id, updates)

    async def delete_document(self, document_id: str, user_id: str) -> None:
        doc = await self.repository.get_document(document_id, user_id)
        if not doc:
            raise ValidationError("Document not found")

        file_path = doc.get("storage_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning("Failed to delete file %s: %s", file_path, e)

        await self.repository.delete_chunks(document_id, user_id)
        await self.repository.delete_document(document_id, user_id)

    async def get_recent_documents(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        return await self.repository.get_recent_documents(user_id, limit)
