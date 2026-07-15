from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import AIProviderUnavailableError, NotFoundError
from app.core.logging import get_logger
from app.prompts import PromptManager, PromptType
from app.providers import AIProvider, GeminiProvider, OllamaProvider
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.services.token_counter import TokenCounter

logger = get_logger(__name__)


class AIService:
    def __init__(self) -> None:
        self.repository = AIRepository()
        self.assignment_repo = AssignmentRepository()
        self.prompt_manager = PromptManager()
        self.token_counter = TokenCounter()

    def _get_providers(self) -> dict[str, AIProvider]:
        return {
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
        }

    async def _resolve_provider(self, preferred: str, user_id: str | None = None) -> AIProvider:
        providers = self._get_providers()
        model_override: str | None = None
        if user_id:
            s = await self.repository.get_ai_settings(user_id)
            model_override = s.get("provider_model") if isinstance(s, dict) else None

        if preferred == "auto":
            for name in ("ollama", "gemini"):
                provider = providers[name]
                if model_override and hasattr(provider, "set_model"):
                    provider.set_model(model_override)
                if await provider.check_availability():
                    logger.info("Auto-routing to provider: %s", name)
                    return provider
        elif preferred in providers:
            provider = providers[preferred]
            if model_override and hasattr(provider, "set_model"):
                provider.set_model(model_override)
            if await provider.check_availability():
                return provider
            raise AIProviderUnavailableError(f"Provider '{preferred}' is not available")

        raise AIProviderUnavailableError("No AI provider is currently available")

    async def _get_settings(self, user_id: str) -> dict[str, Any]:
        s = await self.repository.get_ai_settings(user_id)
        return s if s else {}

    async def _get_academic_context(self, user_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        assignments, total = await self.assignment_repo.list_assignments(
            user_id,
            page=1,
            page_size=10,
            filters={"status": "pending,in_progress"},
        )
        upcoming = [
            a for a in assignments
            if a.get("due_date") and str(a.get("due_date", "")).startswith(now.strftime("%Y"))
        ]
        return {
            "active_assignments": total,
            "upcoming_deadlines": [
                {"title": a.get("title", ""), "due_date": a.get("due_date", ""), "subject": a.get("subject_name", "")}
                for a in upcoming[:5]
            ],
        }

    async def chat(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        conv: dict[str, Any] | None
        if not conversation_id:
            conv = await self.repository.create_conversation(user_id, message[:80])
            conversation_id = conv["id"]
        else:
            conv = await self.repository.get_conversation(conversation_id, user_id)
            if not conv:
                raise NotFoundError("Conversation not found")

        settings_data = await self._get_settings(user_id)
        preferred = str(settings_data.get("preferred_provider", "auto"))
        temperature = float(settings_data.get("temperature", 0.7))
        max_tokens_count = int(settings_data.get("max_tokens", 2048))
        system_prompt_override = settings_data.get("system_prompt")
        academic_context_enabled = bool(settings_data.get("academic_context", True))

        provider = await self._resolve_provider(preferred, user_id)

        await self.repository.create_message(conversation_id, user_id, "user", message, provider.name)

        history = await self.repository.get_messages(conversation_id)
        formatted = await self._format_messages(
            history, user_id, system_prompt_override, academic_context_enabled
        )

        response_text = await provider.generate(formatted, temperature, max_tokens_count)
        token_count = self.token_counter.count_tokens(response_text)

        msg = await self.repository.create_message(
            conversation_id, user_id, "assistant", response_text, provider.name, token_count
        )

        msg_count = await self.repository.get_message_count(conversation_id)
        if msg_count <= 2 and str(conv.get("title", "")).startswith("New conversation"):
            auto_title = message[:80] + ("..." if len(message) > 80 else "")
            await self.repository.update_conversation(
                conversation_id, user_id, {"title": auto_title}
            )

        conv_result = await self.repository.get_conversation(conversation_id, user_id)
        return {"message": msg, "conversation": conv_result}

    async def regenerate(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        conv = await self.repository.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")

        all_messages = await self.repository.get_messages(conversation_id)
        msg_ids = [m["id"] for m in all_messages if m["role"] == "assistant"]

        if message_id not in msg_ids:
            raise NotFoundError("Message not found")

        cutoff = next(
            (i for i, m in enumerate(all_messages) if m["id"] == message_id),
            len(all_messages),
        )
        history = all_messages[:cutoff]

        settings_data = await self._get_settings(user_id)
        preferred = str(settings_data.get("preferred_provider", "auto"))
        temperature = float(settings_data.get("temperature", 0.7))
        max_tokens_count = int(settings_data.get("max_tokens", 2048))
        system_prompt_override = settings_data.get("system_prompt")
        academic_context_enabled = bool(settings_data.get("academic_context", True))

        provider = await self._resolve_provider(preferred, user_id)

        formatted = await self._format_messages(
            history, user_id, system_prompt_override, academic_context_enabled
        )

        response_text = await provider.generate(formatted, temperature, max_tokens_count)
        token_count = self.token_counter.count_tokens(response_text)

        msg = await self.repository.create_message(
            conversation_id, user_id, "assistant", response_text, provider.name, token_count
        )

        conv_result = await self.repository.get_conversation(conversation_id, user_id)
        return {"message": msg, "conversation": conv_result}

    async def _format_messages(
        self,
        history: list[dict[str, Any]],
        user_id: str,
        system_prompt_override: str | None = None,
        academic_context_enabled: bool = True,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

        if system_prompt_override:
            messages.append({"role": "system", "content": system_prompt_override})
        else:
            kwargs: dict[str, Any] = {}
            if academic_context_enabled:
                ac = await self._get_academic_context(user_id)
                kwargs["active_assignments"] = str(ac.get("active_assignments", 0))
                deadlines = ac.get("upcoming_deadlines", [])
                if deadlines:
                    deadline_texts = [
                        f"- {d['title']} (Due: {d['due_date'][:10]})"
                        for d in deadlines
                        if d.get("title")
                    ]
                    kwargs["upcoming_deadlines"] = "\n".join(deadline_texts) if deadline_texts else "None"
                else:
                    kwargs["upcoming_deadlines"] = "None"

            system_content = await self.prompt_manager.build(PromptType.SYSTEM, user_id, **kwargs)
            messages.append({"role": "system", "content": system_content})

        for msg in history:
            role = "assistant" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "content": msg["content"]})

        return messages

    async def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        return await self.repository.list_conversations(user_id)

    async def search_conversations(self, user_id: str, query: str) -> list[dict[str, Any]]:
        return await self.repository.search_conversations(user_id, query)

    async def get_conversation(self, conversation_id: str, user_id: str) -> dict[str, Any]:
        conv = await self.repository.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        messages = await self.repository.get_messages(conversation_id)
        msg_count = await self.repository.get_message_count(conversation_id)
        return {**conv, "messages": messages, "message_count": msg_count}

    async def rename_conversation(self, conversation_id: str, user_id: str, title: str) -> dict[str, Any]:
        conv = await self.repository.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        return await self.repository.update_conversation(conversation_id, user_id, {"title": title})

    async def update_conversation_properties(
        self, conversation_id: str, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        conv = await self.repository.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        allowed = {k: v for k, v in updates.items() if k in ("title", "is_pinned", "is_archived") and v is not None}
        if not allowed:
            return conv
        return await self.repository.update_conversation(conversation_id, user_id, allowed)

    async def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        conv = await self.repository.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        await self.repository.delete_conversation(conversation_id, user_id)

    async def set_message_feedback(
        self, message_id: str, user_id: str, feedback: str | None
    ) -> dict[str, Any]:
        msg = None
        all_convs = await self.repository.list_conversations(user_id)
        for conv in all_convs:
            msgs = await self.repository.get_messages(conv["id"])
            for m in msgs:
                if m["id"] == message_id and m.get("role") == "assistant":
                    msg = m
                    break
        if not msg:
            raise NotFoundError("Message not found")
        return await self.repository.update_message(message_id, user_id, {"feedback": feedback})

    async def edit_message(self, message_id: str, user_id: str, content: str) -> dict[str, Any]:
        return await self.repository.update_message(message_id, user_id, {"content": content})

    async def delete_message(self, message_id: str, user_id: str) -> None:
        await self.repository.delete_message(message_id, user_id)

    async def get_settings(self, user_id: str) -> dict[str, Any]:
        s = await self.repository.get_ai_settings(user_id)
        return s if s else {}

    async def update_settings(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in updates.items() if v is not None}
        if not clean:
            return await self.get_settings(user_id)
        return await self.repository.update_ai_settings(user_id, clean)

    async def check_availability(self) -> dict[str, bool]:
        providers = self._get_providers()
        result: dict[str, bool] = {}
        for name, provider in providers.items():
            try:
                result[name] = await provider.check_availability()
            except Exception:
                result[name] = False
        return result

    async def check_providers_detail(self) -> dict[str, dict[str, Any]]:
        providers = self._get_providers()
        result: dict[str, dict[str, Any]] = {}
        for name, provider in providers.items():
            try:
                detail = await provider.check_availability_detail()
                result[name] = detail
            except Exception as e:
                result[name] = {"available": False, "error": str(e)}
        return result

    async def list_ollama_models(self) -> list[dict[str, Any]]:
        provider = OllamaProvider()
        return await provider.list_models()
