"""Local embedding service using sentence-transformers.

Provides text-to-vector conversion for document chunk indexing and semantic search.
Runs entirely offline with the all-MiniLM-L6-v2 model (~23MB).
"""

from __future__ import annotations

import struct
import time
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model_instance: Any = None


def _load_model() -> Any:
    """Load the sentence-transformer model (lazy, cached)."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", MODEL_NAME)
        start = time.time()
        _model_instance = SentenceTransformer(MODEL_NAME)
        elapsed = time.time() - start
        logger.info("Embedding model loaded in %.2fs", elapsed)
    return _model_instance


class EmbeddingService:
    """Generates embeddings for text using a local sentence-transformer model."""

    @staticmethod
    def is_available() -> bool:
        """Check if the embedding model can be loaded."""
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def embed_text(text: str) -> list[float]:
        """Embed a single text string, return list of floats."""
        model = _load_model()
        embedding = model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()

    @staticmethod
    def embed_batch(texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, return list of float lists."""
        if not texts:
            return []
        model = _load_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=64)
        return [emb.tolist() for emb in embeddings]

    @staticmethod
    def embedding_to_blob(embedding: list[float]) -> bytes:
        """Pack a float list into a compact binary blob using struct."""
        return struct.pack(f"{len(embedding)}f", *embedding)

    @staticmethod
    def blob_to_embedding(blob: bytes) -> list[float]:
        """Unpack a binary blob back to a float list."""
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    @staticmethod
    def get_dimension() -> int:
        """Return the embedding dimension."""
        return EMBEDDING_DIM
