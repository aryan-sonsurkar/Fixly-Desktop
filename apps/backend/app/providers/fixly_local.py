import os
import sys
from collections.abc import AsyncGenerator
from typing import Any

import httpx  # noqa: F401 (kept for parity)

from app.core.logging import get_logger
from app.providers.base import AIProvider

logger = get_logger(__name__)

# Bundled model - stays <500MB total: 352MB GGUF + 32MB app = ~385MB
MODEL_FILENAME = "qwen2-0.5b-instruct-q4_k_m.gguf"
# Will search in dev and bundled locations
CANDIDATE_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"),
    os.path.join(os.path.dirname(sys.executable), "models") if getattr(sys, "frozen", False) else "",
    os.path.join(os.path.dirname(sys.executable), "_internal", "models") if getattr(sys, "frozen", False) else "",
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "Fixly", "models"),
    os.path.join(os.path.expanduser("~"), ".cache", "fixly", "models"),
]

def _find_model() -> str | None:
    for d in CANDIDATE_DIRS:
        if not d:
            continue
        p = os.path.join(d, MODEL_FILENAME)
        if os.path.exists(p) and os.path.getsize(p) > 1024 * 1024:
            return p
    # Also check TAURI resource path for bundled model
    # Tauri extracts resources to <exe_dir>/../resources or next to backend.exe
    for base in [os.path.dirname(sys.executable), os.getcwd(), os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources")]:
        p = os.path.join(base, "models", MODEL_FILENAME)
        if os.path.exists(p):
            return p
        p2 = os.path.join(base, "backend", "models", MODEL_FILENAME)
        if os.path.exists(p2):
            return p2
    return None

class FixlyLocalProvider(AIProvider):
    name = "fixly-local"
    # Used for Diagnostics UI
    required_model = MODEL_FILENAME

    def __init__(self) -> None:
        self.model_path = _find_model()
        self.timeout = 90
        self._llama = None  # lazy load

    def _load_llama(self):  # type: ignore[no-untyped-def]
        if self._llama is not None:
            return self._llama
        if not self.model_path or not os.path.exists(self.model_path):
            return None
        try:
            from llama_cpp import Llama  # type: ignore[import-not-found]

            # low-end friendly: n_ctx 4096, n_threads 4, n_batch 128
            self._llama = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=4,
                n_batch=128,
                verbose=False,
            )
            logger.info("Fixly Local model loaded: %s", self.model_path)
            return self._llama
        except Exception as e:
            logger.warning("Failed to load Fixly Local model: %s", e)
            return None

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        # Run blocking llama call in thread (shared executor pattern)
        import asyncio

        def _sync() -> str:
            llama = self._load_llama()
            if llama is None:
                raise RuntimeError(f"Fixly Local model not found: {MODEL_FILENAME} – run installer with bundled model or place in models/")
            # Convert OpenAI style messages to llama_cpp chat
            # llama_cpp expects list of {"role": "...", "content": "..."}
            try:
                out = llama.create_chat_completion(
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                # out: {"choices": [{"message": {"content": "..."}}]}
                choices = out.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))
                return ""
            except Exception as e:
                logger.error("Fixly Local generate failed: %s", e)
                raise

        return await asyncio.to_thread(_sync)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        # Simple non-streaming fallback – yields once
        text = await self.generate(messages, temperature, max_tokens)
        yield text

    async def check_availability(self) -> bool:
        # Fast check – file exists and llama_cpp importable
        if not self.model_path:
            return False
        try:
            import importlib.util as _u

            if _u.find_spec("llama_cpp") is None:
                return False
            return os.path.exists(self.model_path)
        except Exception:
            return False

    async def check_availability_detail(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "available": False,
            "installed": False,
            "running": False,
            "models": [MODEL_FILENAME] if self.model_path else [],
            "error": None,
            "model_count": 1 if self.model_path else 0,
            "required_model": MODEL_FILENAME,
        }
        if not self.model_path:
            result["error"] = f"Bundled model not found: {MODEL_FILENAME} – reinstall Fixly 1.0.0+ installer or place GGUF in backend/models/"
            return result
        try:
            import importlib.util as _u

            if _u.find_spec("llama_cpp") is None:
                result["installed"] = True
                result["error"] = "llama-cpp-python not installed – pip install llama-cpp-python"
                return result
            result["installed"] = True
            result["running"] = True
            result["available"] = True
        except Exception as e:
            result["error"] = str(e)
        return result

    async def list_models(self) -> list[dict[str, Any]]:
        if self.model_path:
            try:
                sz = os.path.getsize(self.model_path)
                return [{"name": MODEL_FILENAME, "size": sz, "modified_at": ""}]
            except Exception:
                pass
        return []
