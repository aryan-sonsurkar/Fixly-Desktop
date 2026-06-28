import time
from typing import Any

from app.core.logging import get_logger
from app.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class OCRService:
    """Modular OCR service. The engine is replaceable — swap the _extract method."""

    def __init__(self) -> None:
        self.repository = DocumentRepository()

    async def process_image(
        self, document_id: str, user_id: str, file_path: str, file_type: str
    ) -> dict[str, Any]:
        start = time.time()

        extracted_text = await self._extract_text(file_path, file_type)
        confidence = self._estimate_confidence(extracted_text)
        processing_time = int((time.time() - start) * 1000)

        result = await self.repository.create_ocr_result(user_id, {
            "document_id": document_id,
            "user_id": user_id,
            "extracted_text": extracted_text,
            "confidence": confidence,
            "processing_time_ms": processing_time,
            "engine": "builtin",
        })

        await self.repository.update_document(document_id, user_id, {
            "status": "processed",
            "processing_time_ms": processing_time,
        })

        return result

    async def _extract_text(self, file_path: str, file_type: str) -> str:
        """Built-in OCR extraction. Replace this with Tesseract/OCRmyPDF/etc."""
        logger.info("Built-in OCR: extracting text from %s (%s)", file_path, file_type)
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            return await self._simple_ocr(raw, file_type)
        except Exception as e:
            logger.error("OCR extraction failed for %s: %s", file_path, e)
            return f"[OCR processing failed: {e}]"

    async def _simple_ocr(self, data: bytes, file_type: str) -> str:
        """Placeholder OCR — returns metadata. Override with real OCR engine."""
        return (
            f"[OCR Processed: {file_type.upper()} file, {len(data)} bytes]\n"
            f"[Content extracted via built-in OCR engine]\n"
            f"[Install Tesseract or configure an external OCR provider for full text extraction]"
        )

    def _estimate_confidence(self, text: str) -> float:
        if not text or text.startswith("[OCR"):
            return 0.0
        return 0.85


class TesseractOCRService(OCRService):
    """OCR service using Tesseract (install required: `pip install pytesseract`)."""

    async def _extract_text(self, file_path: str, file_type: str) -> str:
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip() or "[No text detected in image]"
        except ImportError:
            logger.warning("pytesseract not installed, falling back to built-in OCR")
            return await super()._extract_text(file_path, file_type)
        except Exception as e:
            logger.error("Tesseract OCR failed: %s", e)
            return f"[OCR Error: {e}]"
