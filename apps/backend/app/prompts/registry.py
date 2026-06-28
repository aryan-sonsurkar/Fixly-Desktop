import importlib
import pkgutil
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptType(str, Enum):
    SYSTEM = "system"
    ASSIGNMENT = "assignment"
    CODING = "coding"
    STUDY = "study"
    SUMMARIZE = "summarize"
    BRIEFING = "briefing"
    PDF = "pdf"
    SCREENSHOT = "screenshot"
    OCR = "ocr"
    EMAIL = "email"
    PLANNER = "planner"


@dataclass
class PromptTemplate:
    name: str
    version: str
    description: str
    author: str
    last_updated: str
    template: str
    requires_context: bool = True


class PromptRegistry:
    def __init__(self) -> None:
        self._entries: dict[PromptType, PromptTemplate] = {}

    def register(self, prompt_type: PromptType, template: PromptTemplate) -> None:
        self._entries[prompt_type] = template

    def get(self, prompt_type: PromptType) -> PromptTemplate:
        if prompt_type not in self._entries:
            raise KeyError(f"Unknown prompt type: {prompt_type}")
        return self._entries[prompt_type]

    @property
    def types(self) -> list[PromptType]:
        return list(self._entries.keys())


_REGISTRY = PromptRegistry()
_registry_initialized = False


def init_registry() -> None:
    global _registry_initialized
    if _registry_initialized:
        return
    auto_discover()
    _registry_initialized = True


def get_registry() -> PromptRegistry:
    if not _registry_initialized:
        init_registry()
    return _REGISTRY


def auto_discover() -> None:
    import app.prompts.templates as templates_pkg

    for _importer, modname, ispkg in pkgutil.iter_modules(templates_pkg.__path__):
        if ispkg:
            continue
        full_name = f"app.prompts.templates.{modname}"
        try:
            module = importlib.import_module(full_name)
        except Exception as e:
            logger.warning("Failed to import prompt template %s: %s", full_name, e)
            continue
        prompt = getattr(module, "PROMPT", None)
        prompt_type = getattr(module, "PROMPT_TYPE", None)
        if prompt is not None and prompt_type is not None:
            _REGISTRY.register(prompt_type, prompt)
            logger.debug("Registered prompt: %s", prompt_type.value)
