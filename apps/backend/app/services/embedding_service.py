"""Local embedding service using sentence-transformers.

Provides text-to-vector conversion for document chunk indexing and semantic search.
Runs entirely offline with the all-MiniLM-L6-v2 model (~23MB).
"""

from __future__ import annotations

import os
import struct
import time
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model_instance: Any = None


def _bundled_model_dir() -> str | None:
    """Path to the pre-bundled embedding model, if shipped with the install.

    Resolution order: FIXLY_EMBEDDINGS_DIR env (set by the Tauri launcher to
    <resources>/backend/models/embeddings) then the dev checkout layout.
    """
    candidates = []
    env_dir = os.environ.get("FIXLY_EMBEDDINGS_DIR")
    if env_dir:
        candidates.append(Path(env_dir) / MODEL_NAME)
    candidates.append(
        Path(__file__).resolve().parents[2] / "models" / "embeddings" / MODEL_NAME
    )
    for cand in candidates:
        if (cand / "config.json").exists():
            return str(cand)
    return None


def _load_model() -> Any:
    """Load the sentence-transformer model (lazy, cached)."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer

        source = _bundled_model_dir() or MODEL_NAME
        logger.info("Loading embedding model: %s", source)
        start = time.time()
        _model_instance = SentenceTransformer(source)
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
