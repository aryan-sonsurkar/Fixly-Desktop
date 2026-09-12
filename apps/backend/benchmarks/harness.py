"""Core benchmark harness for Qwen model capability evaluation.

Provides deterministic model invocation, metrics computation, and
machine-readable result output.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

MODEL_FILE = "qwen2-0.5b-instruct-q4_k_m.gguf"
CANDIDATE_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"),
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "Fixly", "models"),
    os.path.join(os.path.expanduser("~"), ".cache", "fixly", "models"),
]

# Deterministic generation settings for benchmarking
BENCH_TEMP = 0.0
BENCH_MAX_TOKENS = 512
BENCH_N_CTX = 4096
BENCH_N_THREADS = 4


def find_model() -> str | None:
    for d in CANDIDATE_DIRS:
        p = os.path.join(d, MODEL_FILE)
        if os.path.isfile(p) and os.path.getsize(p) > 1024 * 1024:
            return p
    return None


# ---------------------------------------------------------------------------
# Model wrapper
# ---------------------------------------------------------------------------


class QwenBench:
    """Thin wrapper around llama-cpp-python for benchmarking."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path or find_model()
        if not self.model_path:
            raise FileNotFoundError(f"Model {MODEL_FILE} not found")
        self._llama = None
        self.load_time = 0.0

    def load(self) -> float:
        if self._llama is not None:
            return self.load_time
        t0 = time.perf_counter()
        from llama_cpp import Llama

        self._llama = Llama(
            model_path=self.model_path,
            n_ctx=BENCH_N_CTX,
            n_threads=BENCH_N_THREADS,
            n_batch=128,
            verbose=False,
        )
        self.load_time = time.perf_counter() - t0
        return self.load_time

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = BENCH_TEMP,
        max_tokens: int = BENCH_MAX_TOKENS,
    ) -> tuple[str, float]:
        """Generate completion. Returns (text, latency_seconds)."""
        self.load()
        t0 = time.perf_counter()
        out = self._llama.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.perf_counter() - t0
        choices = out.get("choices", [])
        if choices:
            text = str(choices[0].get("message", {}).get("content", "") or "").strip()
            return text, latency
        return "", latency

    def get_model_size_mb(self) -> float:
        return os.path.getsize(self.model_path) / (1024 * 1024)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def system_prompt(text: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": text}]


def chat(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


def extract_json(text: str) -> dict[str, Any] | None:
    """Try to extract a JSON object from model output."""
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    # Try extracting first {...} block
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, TypeError):
            pass
    # Try stripping markdown code fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def extract_json_array(text: str) -> list[Any] | None:
    """Try to extract a JSON array from model output."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkResult:
    name: str
    total: int = 0
    correct: int = 0
    accuracy: float = 0.0
    details: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def finalize(self) -> None:
        self.accuracy = self.correct / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Gate3Report:
    model_path: str = ""
    model_size_mb: float = 0.0
    load_time_s: float = 0.0
    latency_cold_ms: float = 0.0
    latency_warm_ms: float = 0.0
    intent: BenchmarkResult = field(default_factory=lambda: BenchmarkResult("intent"))
    json_output: BenchmarkResult = field(default_factory=lambda: BenchmarkResult("json"))
    tool_select: BenchmarkResult = field(default_factory=lambda: BenchmarkResult("tool_select"))
    planning: BenchmarkResult = field(default_factory=lambda: BenchmarkResult("planning"))
    safety: BenchmarkResult = field(default_factory=lambda: BenchmarkResult("safety"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_path": self.model_path,
            "model_size_mb": self.model_size_mb,
            "load_time_s": self.load_time_s,
            "latency_cold_ms": self.latency_cold_ms,
            "latency_warm_ms": self.latency_warm_ms,
            "benchmarks": {
                "intent": self.intent.to_dict(),
                "json_output": self.json_output.to_dict(),
                "tool_select": self.tool_select.to_dict(),
                "planning": self.planning.to_dict(),
                "safety": self.safety.to_dict(),
            },
        }
