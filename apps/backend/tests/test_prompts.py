from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.prompts import PromptManager, PromptTemplate, PromptType, get_registry
from app.prompts.registry import PromptRegistry
from app.prompts.utils import count_placeholders, resolve_variables


class TestPromptRegistry:
    def setup_method(self) -> None:
        self.registry = PromptRegistry()

    def test_register_and_get(self) -> None:
        template = PromptTemplate(
            name="test",
            version="1.0.0",
            description="Test template",
            author="Test",
            last_updated="2026-06-26",
            template="Hello {user_name}",
        )
        self.registry.register(PromptType.SYSTEM, template)
        result = self.registry.get(PromptType.SYSTEM)
        assert result.name == "test"
        assert result.template == "Hello {user_name}"

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown prompt type"):
            self.registry.get(PromptType.SYSTEM)

    def test_types_property(self) -> None:
        t1 = PromptTemplate(name="a", version="1", description="", author="", last_updated="", template="a")
        t2 = PromptTemplate(name="b", version="1", description="", author="", last_updated="", template="b")
        self.registry.register(PromptType.SYSTEM, t1)
        self.registry.register(PromptType.CODING, t2)
        assert PromptType.SYSTEM in self.registry.types
        assert PromptType.CODING in self.registry.types
        assert PromptType.STUDY not in self.registry.types

    def test_get_registry_singleton(self) -> None:
        assert get_registry() is get_registry()


class TestResolveVariables:
    def test_basic_replacement(self) -> None:
        result = resolve_variables("Hello {user_name}", context={"profile": {"display_name": "Alice"}, "subjects": []})
        assert "Hello Alice" in result

    def test_missing_variable_preserved(self) -> None:
        result = resolve_variables("Hello {unknown_var}")
        assert "{unknown_var}" in result

    def test_kwargs_override(self) -> None:
        result = resolve_variables("Hello {user_name}", context={"profile": {"display_name": "Alice"}, "subjects": []}, kwargs={"user_name": "Bob"})
        assert "Hello Bob" in result

    def test_current_date_injected(self) -> None:
        result = resolve_variables("Date: {current_date}")
        assert date.today().isoformat() in result

    def test_subject_list(self) -> None:
        context = {
            "profile": {},
            "subjects": [{"name": "Math"}, {"name": "Physics"}],
        }
        result = resolve_variables("Subjects: {subjects}", context=context)
        assert "Math, Physics" in result

    def test_empty_context_defaults(self) -> None:
        context = {"profile": {}, "subjects": []}
        result = resolve_variables("Hello {user_name}, studying {branch}", context=context)
        assert "Hello Student" in result

    def test_all_profile_variables(self) -> None:
        context = {
            "profile": {
                "display_name": "Alice",
                "full_name": "Alice Smith",
                "education_type": "engineering",
                "branch_stream": "Computer Science",
                "education_year": "2nd Year",
                "college_name": "MIT",
            },
            "subjects": [{"name": "Data Structures"}],
        }
        result = resolve_variables(
            "{user_name} - {education_type} - {branch} - {year} - {college} - {subjects}",
            context=context,
        )
        assert "Alice" in result
        assert "engineering" in result
        assert "Computer Science" in result
        assert "2nd Year" in result
        assert "MIT" in result
        assert "Data Structures" in result

    def test_full_name_fallback(self) -> None:
        context = {"profile": {"full_name": "Bob Johnson"}, "subjects": []}
        result = resolve_variables("Hello {user_name}", context=context)
        assert "Bob Johnson" in result


class TestCountPlaceholders:
    def test_count_placeholders(self) -> None:
        placeholders = count_placeholders("Hello {user_name}, your {subject} class is at {time}")
        assert placeholders == ["user_name", "subject", "time"]

    def test_no_placeholders(self) -> None:
        assert count_placeholders("Hello world") == []


class TestPromptManagerBuild:
    @pytest.mark.asyncio
    async def test_build_with_context(self) -> None:
        registry = get_registry()
        previous = registry.get(PromptType.SYSTEM)

        manager = PromptManager()
        template = PromptTemplate(
            name="greeting",
            version="1.0.0",
            description="Greeting",
            author="Test",
            last_updated="2026-06-26",
            template="Hello {user_name}, welcome to {course}!",
        )
        manager.register_prompt(PromptType.SYSTEM, template)

        mock_profile = AsyncMock()
        mock_profile.get_profile = AsyncMock(return_value={"display_name": "Alice"})
        mock_profile.get_settings = AsyncMock(return_value={})
        mock_profile.upsert_settings = AsyncMock(return_value={})
        manager.profile_repo = mock_profile

        mock_subject = AsyncMock()
        mock_subject.list_subjects = AsyncMock(return_value=[])
        manager.subject_repo = mock_subject

        result = await manager.build(PromptType.SYSTEM, "user-123", course="Physics 101")
        assert "Alice" in result
        assert "Physics 101" in result

        registry.register(PromptType.SYSTEM, previous)

    @pytest.mark.asyncio
    async def test_build_without_context(self) -> None:
        registry = get_registry()
        previous = registry.get(PromptType.SYSTEM)

        manager = PromptManager()
        template = PromptTemplate(
            name="simple",
            version="1.0.0",
            description="Simple",
            author="Test",
            last_updated="2026-06-26",
            template="Static prompt without variables",
            requires_context=False,
        )
        manager.register_prompt(PromptType.SYSTEM, template)
        result = await manager.build(PromptType.SYSTEM)
        assert result == "Static prompt without variables"

        registry.register(PromptType.SYSTEM, previous)

    @pytest.mark.asyncio
    async def test_auto_discover_registers_all_templates(self) -> None:
        registry = get_registry()
        all_types = list(PromptType)
        for pt in all_types:
            assert registry.get(pt) is not None
            assert registry.get(pt).name is not None

    @pytest.mark.asyncio
    async def test_template_metadata(self) -> None:
        registry = get_registry()
        for pt in PromptType:
            tpl = registry.get(pt)
            assert tpl.version
            assert tpl.description
            assert tpl.author
            assert tpl.last_updated
            assert len(tpl.template) > 10
            assert "{" in tpl.template  # has variables
