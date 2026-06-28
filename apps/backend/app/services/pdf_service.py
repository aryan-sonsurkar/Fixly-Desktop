import time
from typing import Any

from app.core.logging import get_logger
from app.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class PDFService:
    def __init__(self) -> None:
        self.repository = DocumentRepository()

    async def extract_text(self, file_path: str) -> str:
        try:
            import PyPDF2

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                return "\n\n".join(pages) if pages else "[No text extracted from PDF]"
        except ImportError:
            logger.warning("PyPDF2 not installed, trying pypdf...")
        except Exception as e:
            logger.error("PyPDF2 extraction failed: %s", e)

        try:
            import pypdf

            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                return "\n\n".join(pages) if pages else "[No text extracted from PDF]"
        except ImportError:
            logger.warning("pypdf not installed either, falling back to placeholder")
        except Exception as e:
            logger.error("pypdf extraction failed: %s", e)

        return f"[PDF file: {file_path} — install PyPDF2 or pypdf for text extraction]"

    async def get_page_count(self, file_path: str) -> int:
        try:
            import PyPDF2

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return len(reader.pages)
        except ImportError:
            pass
        try:
            import pypdf

            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                return len(reader.pages)
        except ImportError:
            pass
        return 0

    async def extract_metadata(self, file_path: str) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        try:
            import PyPDF2

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata
                if info:
                    for k, v in info.items():
                        key = k.lstrip("/").lower()
                        meta[key] = str(v) if v else ""
        except Exception:
            pass
        return meta

    async def chunk_text(
        self, text: str, chunk_size: int = 2000, overlap: int = 200
    ) -> list[dict[str, Any]]:
        if not text or text.startswith("[No text") or text.startswith("[PDF file"):
            return [{
                "chunk_index": 0,
                "chunk_type": "text",
                "content": text or "[Empty document]",
                "heading": None,
                "page_number": None,
                "token_count": len(text.split()) if text else 0,
            }]

        chunks: list[dict[str, Any]] = []
        words = text.split()
        start = 0
        index = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            # Simple heading detection
            heading = None
            lines = chunk_text.split("\n")
            for line in lines[:3]:
                stripped = line.strip()
                if stripped and (stripped.isupper() or len(stripped) < 100):
                    heading = stripped[:80]
                    break

            token_count = len(chunk_text.split())
            chunks.append({
                "chunk_index": index,
                "chunk_type": "heading" if heading else "text",
                "content": chunk_text,
                "heading": heading,
                "page_number": None,
                "token_count": token_count,
            })

            index += 1
            start = end - overlap if (end < len(words)) else end

        return chunks

    async def process_pdf(
        self, document_id: str, user_id: str, file_path: str
    ) -> dict[str, Any]:
        start = time.time()

        text = await self.extract_text(file_path)
        page_count = await self.get_page_count(file_path)
        metadata = await self.extract_metadata(file_path)
        chunks = await self.chunk_text(text)

        processing_time = int((time.time() - start) * 1000)

        for chunk in chunks:
            chunk["document_id"] = document_id
            chunk["user_id"] = user_id

        if chunks:
            await self.repository.create_chunks(chunks)

        await self.repository.update_document(document_id, user_id, {
            "status": "processed",
            "page_count": page_count,
            "processing_time_ms": processing_time,
        })

        return {
            "document_id": document_id,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "total_tokens": sum(c.get("token_count", 0) for c in chunks),
            "processing_time_ms": processing_time,
            "metadata": metadata,
        }
