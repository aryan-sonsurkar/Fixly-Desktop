import time
from typing import Any

from app.core.logging import get_logger
from app.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class PDFService:
    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.repository = DocumentRepository(access_token=access_token)

    async def extract_text(self, file_path: str) -> str:
        pages = await self.extract_pages(file_path)
        texts = [t for _, t in pages if t.strip()]
        if texts:
            return "\n\n".join(texts)
        if pages:
            return "[No text layer found in PDF — likely a scanned/image PDF]"
        return "[PDF extraction failed: no pages readable]"

    async def extract_pages(self, file_path: str) -> list[tuple[int, str]]:
        """Extract text per page as (page_number, text) with 1-based pages."""
        try:
            from pypdf import PdfReader

            out: list[tuple[int, str]] = []
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for i, page in enumerate(reader.pages, start=1):
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""
                    if text.strip():
                        out.append((i, text.strip()))
            return out
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            return []

    async def get_page_count(self, file_path: str) -> int:
        try:
            from pypdf import PdfReader

            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return len(reader.pages)
        except Exception as e:
            logger.error("Failed to read PDF page count: %s", e)
            return 0

    async def extract_metadata(self, file_path: str) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        try:
            from pypdf import PdfReader

            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                info = reader.metadata
                if info:
                    for k, v in info.items():
                        key = k.lstrip("/").lower()
                        meta[key] = str(v) if v else ""
        except Exception:
            pass
        return meta

    async def chunk_text(
        self, text: str, chunk_size: int = 2000, overlap: int = 200,
        page_number: int | None = None,
    ) -> list[dict[str, Any]]:
        if not text or text.startswith("[No text") or text.startswith("[PDF extraction"):
            return []

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
                "page_number": page_number,
                "token_count": token_count,
            })

            index += 1
            start = end - overlap if (end < len(words)) else end

        return chunks

    async def chunk_pages(
        self, pages: list[tuple[int, str]], chunk_size: int = 2000, overlap: int = 200
    ) -> list[dict[str, Any]]:
        """Chunk per-page text, preserving page numbers for citations."""
        chunks: list[dict[str, Any]] = []
        for page_number, text in pages:
            page_chunks = await self.chunk_text(
                text, chunk_size=chunk_size, overlap=0, page_number=page_number
            )
            for chunk in page_chunks:
                chunk["chunk_index"] = len(chunks)
                chunks.append(chunk)
        return chunks

    async def process_pdf(
        self, document_id: str, user_id: str, file_path: str
    ) -> dict[str, Any]:
        start = time.time()

        pages = await self.extract_pages(file_path)
        page_count = await self.get_page_count(file_path)
        metadata = await self.extract_metadata(file_path)
        chunks = await self.chunk_pages(pages)
        has_text = len(chunks) > 0

        processing_time = int((time.time() - start) * 1000)

        for chunk in chunks:
            chunk["document_id"] = document_id
            chunk["user_id"] = user_id

        if chunks:
            await self.repository.create_chunks(chunks)

        # "empty" is distinct from "failed": the file is fine but has no
        # extractable text (e.g. scanned PDF). Never index placeholders.
        await self.repository.update_document(document_id, user_id, {
            "status": "empty" if not has_text else "processing",
            "page_count": page_count,
            "processing_time_ms": processing_time,
        })

        return {
            "document_id": document_id,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "has_text": has_text,
            "total_tokens": sum(c.get("token_count", 0) for c in chunks),
            "processing_time_ms": processing_time,
            "metadata": metadata,
        }
