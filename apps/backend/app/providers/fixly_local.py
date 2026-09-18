import os
import sys
import threading
from collections.abc import AsyncGenerator, Iterator
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
    os.path.join(os.path.dirname(sys.executable), "..", "models") if getattr(sys, "frozen", False) else "",
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
    bases = [
        os.path.dirname(sys.executable),
        os.getcwd(),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources"),
    ]
    for base in bases:
        p = os.path.join(base, "models", MODEL_FILENAME)
        if os.path.exists(p):
            return p
        p2 = os.path.join(base, "backend", "models", MODEL_FILENAME)
        if os.path.exists(p2):
            return p2
    return None

# Tiny-model prompt budget: Qwen2 0.5B (n_ctx 4096) returns empty completions
# on oversized prompts. Keep system + recent tail under this char budget.
PROMPT_CHAR_BUDGET = 8000
# Upper bound for a 0.5B local model; callers may request less.
MAX_TOKENS_CAP = 1024


def _truncate_to_budget(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Drop oldest non-system messages until the prompt fits the tiny-model budget."""
    total = sum(len(m.get("content", "")) for m in messages)
    if total <= PROMPT_CHAR_BUDGET:
        return messages
    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]
    while rest and sum(len(m.get("content", "")) for m in system + rest) > PROMPT_CHAR_BUDGET:
        rest.pop(0)
    return system + rest


class FixlyLocalProvider(AIProvider):
    name = "fixly-local"
    # Used for Diagnostics UI
    required_model = MODEL_FILENAME

    # Process-wide resident model: load once, reuse for every request.
    _shared_llama: Any | None = None
    _shared_load_error: str | None = None
    _load_lock = threading.Lock()

    def __init__(self) -> None:
        self.model_path = _find_model()
        self.timeout = 90

    @classmethod
    def is_resident(cls) -> bool:
        return cls._shared_llama is not None

    def _load_llama(self) -> Any | None:
        if FixlyLocalProvider._shared_llama is not None:
            return FixlyLocalProvider._shared_llama
        if not self.model_path or not os.path.exists(self.model_path):
            return None
        with FixlyLocalProvider._load_lock:
            if FixlyLocalProvider._shared_llama is not None:
                return FixlyLocalProvider._shared_llama
            try:
                from llama_cpp import Llama

                # low-end friendly: n_ctx 4096, n_threads 4, n_batch 128
                FixlyLocalProvider._shared_llama = Llama(
                    model_path=self.model_path,
                    n_ctx=4096,
                    n_threads=4,
                    n_batch=128,
                    verbose=False,
                )
                FixlyLocalProvider._shared_load_error = None
                logger.info("Fixly Local model loaded: %s", self.model_path)
                return FixlyLocalProvider._shared_llama
            except Exception as e:
                FixlyLocalProvider._shared_load_error = str(e)
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
                logger.warning("Fixly Local generate called with engine unavailable")
                raise RuntimeError("Fixly AI is currently unavailable. Please try again in a moment.")
            capped = min(max_tokens, MAX_TOKENS_CAP)
            budgeted = _truncate_to_budget(messages)
            try:
                out = llama.create_chat_completion(
                    messages=budgeted,
                    temperature=temperature,
                    max_tokens=capped,
                )
                choices = out.get("choices", [])
                if choices:
                    text = str(choices[0].get("message", {}).get("content", "") or "").strip()
                    if text:
                        return text
                    # Tiny model sometimes returns empty on long system prompts — retry with shorter context
                    short_msgs = [m for m in budgeted if m["role"] != "system"]
                    if short_msgs:
                        short_msgs.insert(0, {
                            "role": "system",
                            "content": "You are Fixly AI, a helpful academic assistant.",
                        })
                        try:
                            out2 = llama.create_chat_completion(
                                messages=short_msgs,
                                temperature=0.8,
                                max_tokens=capped,
                            )
                            c2 = out2.get("choices", [])
                            if c2:
                                t2 = str(c2[0].get("message", {}).get("content", "") or "").strip()
                                if t2:
                                    return t2
                        except Exception:
                            pass
                    return text
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
        import asyncio

        def _sync_gen() -> Iterator[str]:
            llama = self._load_llama()
            if llama is None:
                raise RuntimeError("Fixly AI is currently unavailable. Please try again in a moment.")
            capped = min(max_tokens, MAX_TOKENS_CAP)
            budgeted = _truncate_to_budget(messages)

            def _stream_from(msgs: list[dict[str, str]]) -> Iterator[str]:
                # Try streaming, fallback to single yield if not supported
                try:
                    stream = llama.create_chat_completion(
                        messages=msgs,
                        temperature=temperature,
                        max_tokens=capped,
                        stream=True,
                    )
                    for chunk in stream:
                        # chunk: {"choices": [{"delta": {"content": "..."}}]}
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                    return
                except TypeError:
                    # older llama_cpp without stream support
                    pass
                # fallback
                out = llama.create_chat_completion(
                    messages=msgs,
                    temperature=temperature,
                    max_tokens=capped,
                )
                choices = out.get("choices", [])
                if choices:
                    yield str(choices[0].get("message", {}).get("content", ""))

            yielded_any = False
            for tok in _stream_from(budgeted):
                yielded_any = True
                yield tok
            if not yielded_any:
                # Tiny model sometimes returns empty on long prompts — retry short
                logger.info("Fixly Local stream empty, retrying with short context")
                short_msgs = [m for m in budgeted if m.get("role") != "system"]
                if short_msgs:
                    short_msgs.insert(0, {
                        "role": "system",
                        "content": "You are Fixly AI, a helpful academic assistant.",
                    })
                    for tok in _stream_from(short_msgs):
                        yield tok

        # Bridge sync generator to async via thread queue.
        # Stream errors are re-raised (not masked) so the API returns an
        # honest error instead of a fake friendly response.
        import queue
        import threading

        q: queue.Queue[str | Exception | None] = queue.Queue()
        done = threading.Event()

        def _thread() -> None:
            try:
                gen = _sync_gen()
                # _sync_gen is a generator, iterate
                for tok in gen:
                    q.put(tok)
            except Exception as e:
                logger.error("Fixly Local stream failed: %s", e)
                q.put(e)
            finally:
                q.put(None)
                done.set()

        thread = threading.Thread(target=_thread, daemon=True)
        thread.start()
        while not done.is_set() or not q.empty():
            try:
                tok = await asyncio.to_thread(q.get, True, 0.05)
            except Exception:
                await asyncio.sleep(0.02)
                continue
            if tok is None:
                if done.is_set() and q.empty():
                    break
                continue
            if isinstance(tok, Exception):
                raise tok
            yield tok

    async def check_availability(self) -> bool:
        # Fast check – model file exists and native engine actually imports
        # (find_spec alone can lie when the bundled DLL fails to load).
        if not self.model_path:
            return False
        try:
            from llama_cpp import Llama  # noqa: F401

            return os.path.exists(self.model_path)
        except Exception:
            return False

    async def check_availability_detail(self) -> dict[str, Any]:
        # Student-facing `error` copy only — technical details go to logs.
        result: dict[str, Any] = {
            "name": self.name,
            "available": False,
            "installed": False,
            "running": False,
            "models": [MODEL_FILENAME] if self.model_path else [],
            "error": None,
            "reason": "unavailable",
            "model_count": 1 if self.model_path else 0,
            "required_model": MODEL_FILENAME,
        }
        if not self.model_path:
            logger.warning("Fixly Local bundled model missing (searched candidate dirs)")
            result["error"] = "Fixly AI couldn't start. Restart Fixly or check for an available update."
            result["reason"] = "needs_update"
            return result
        try:
            # Actually import the native engine: find_spec alone can succeed
            # while the bundled DLL fails to load (frozen builds). Import is
            # cached by sys.modules, so this is cheap after first call.
            from llama_cpp import Llama  # noqa: F401

            result["installed"] = True
            result["model_loaded"] = FixlyLocalProvider.is_resident()
            result["running"] = True
            result["available"] = True
            result["error"] = None
            result["reason"] = "ready"
        except Exception as e:
            logger.warning("Fixly Local runtime unavailable (native engine failed): %s", e)
            result["installed"] = True
            result["error"] = "Fixly AI couldn't start. Restart Fixly or check for an available update."
            result["reason"] = "needs_update"
        return result

    async def list_models(self) -> list[dict[str, Any]]:
        if self.model_path:
            try:
                sz = os.path.getsize(self.model_path)
                return [{"name": MODEL_FILENAME, "size": sz, "modified_at": ""}]
            except Exception:
                pass
        return []
