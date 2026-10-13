"""Local embedding service using ONNX Runtime.

all-MiniLM-L6-v2 weights run as pre-exported ONNX (Xenova) with mean
pooling + L2 normalization — numerically equivalent to the previous
sentence-transformers path at a fraction of the footprint (no torch:
~300MB runtime instead of ~3GB). Public API and 384-dim output are
unchanged. Runs entirely offline; nothing is downloaded at runtime.
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
MODEL_FILE = "model.onnx"
TOKENIZER_FILE = "tokenizer.json"
EMBEDDING_DIM = 384
_MAX_SEQ_LENGTH = 512
_BATCH_CHUNK = 64
# Low-end friendly: mirror the local-LLM convention (4 inference threads).
_INTRA_OP_THREADS = 4

_model_instance: tuple[Any, Any] | None = None


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


def _load_model() -> tuple[Any, Any]:
    """Load the ONNX session + tokenizer (lazy, cached).

    Returns (session, tokenizer). Heavy imports stay inside so merely
    importing this module never requires onnxruntime/numpy.
    """
    global _model_instance
    if _model_instance is None:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        model_dir = _bundled_model_dir()
        if model_dir is None:
            raise RuntimeError(
                "Embedding model directory not found "
                "(FIXLY_EMBEDDINGS_DIR or models/embeddings/all-MiniLM-L6-v2)."
            )
        onnx_path = os.path.join(model_dir, MODEL_FILE)
        tok_path = os.path.join(model_dir, TOKENIZER_FILE)
        if not os.path.exists(onnx_path) or os.path.getsize(onnx_path) < 10 * 1024 * 1024:
            raise RuntimeError(f"Embedding model missing or truncated: {onnx_path}")
        if not os.path.exists(tok_path):
            raise RuntimeError(f"Embedding tokenizer missing: {tok_path}")
        logger.info("Loading embedding model: %s", model_dir)
        start = time.time()
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = _INTRA_OP_THREADS
        opts.inter_op_num_threads = 1
        session = ort.InferenceSession(
            onnx_path, sess_options=opts, providers=["CPUExecutionProvider"]
        )
        tokenizer = Tokenizer.from_file(tok_path)
        tokenizer.enable_truncation(max_length=_MAX_SEQ_LENGTH)
        tokenizer.enable_padding()
        _model_instance = (session, tokenizer)
        elapsed = time.time() - start
        logger.info("Embedding model loaded in %.2fs", elapsed)
    return _model_instance


def _run_batch(session: Any, tokenizer: Any, texts: list[str]) -> list[list[float]]:
    """Mean-pool + L2-normalize one padded batch (mirrors ST defaults)."""
    import numpy as np

    enc = tokenizer.encode_batch(texts)
    ids = np.array([e.ids for e in enc], dtype=np.int64)
    mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
    inputs: dict[str, Any] = {"input_ids": ids, "attention_mask": mask}
    if "token_type_ids" in {i.name for i in session.get_inputs()}:
        type_ids = [(e.type_ids or [0] * len(e.ids)) for e in enc]
        inputs["token_type_ids"] = np.array(type_ids, dtype=np.int64)
    hidden = session.run(None, inputs)[0]
    weights = mask[..., None].astype(np.float32)
    pooled = (hidden * weights).sum(axis=1) / weights.sum(axis=1).clip(min=1e-9)
    norms = np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-12)
    out: list[list[float]] = (pooled / norms).tolist()
    return out


class EmbeddingService:
    """Generates embeddings for text using a local ONNX embedding model."""

    @staticmethod
    def is_available() -> bool:
        """Check if the embedding runtime can be loaded."""
        try:
            import onnxruntime  # noqa: F401
            import tokenizers  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def embed_text(text: str) -> list[float]:
        """Embed a single text string, return list of floats."""
        session, tokenizer = _load_model()
        return _run_batch(session, tokenizer, [text])[0]

    @staticmethod
    def embed_batch(texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, return list of float lists."""
        if not texts:
            return []
        session, tokenizer = _load_model()
        out: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_CHUNK):
            out.extend(_run_batch(session, tokenizer, texts[i : i + _BATCH_CHUNK]))
        return out

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
