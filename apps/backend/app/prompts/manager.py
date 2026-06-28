from typing import Any

from app.core.logging import get_logger
from app.prompts.registry import PromptRegistry, PromptTemplate, PromptType, get_registry
from app.prompts.utils import resolve_variables
from app.repositories.profile_repository import ProfileRepository
from app.repositories.subject_repository import SubjectRepository

logger = get_logger(__name__)


class PromptManager:
    def __init__(self) -> None:
        self.profile_repo = ProfileRepository()
        self.subject_repo = SubjectRepository()
        self.registry: PromptRegistry = get_registry()

    async def build(
        self,
        prompt_type: PromptType,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        template = self.registry.get(prompt_type)

        user_context = None
        if template.requires_context and user_id:
            user_context = await self._load_user_context(user_id)

        return resolve_variables(template.template, user_context, kwargs)

    async def _load_user_context(self, user_id: str) -> dict[str, Any]:
        profile = await self.profile_repo.get_profile(user_id)
        subjects = await self.subject_repo.list_subjects(user_id)
        return {
            "profile": profile or {},
            "subjects": subjects or [],
        }

    def register_prompt(self, prompt_type: PromptType, template: PromptTemplate) -> None:
        self.registry.register(prompt_type, template)
