"""Tool Registry for Fixly AI.

Central registry of all tools the AI can use. Each tool is declared
with its authorization level, required parameters, and safety metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ToolCategory(str, Enum):
    READING = "reading"
    WRITING = "writing"
    DESTRUCTIVE = "destructive"
    SCHEDULING = "scheduling"
    COMMUNICATION = "communication"
    WEB = "web"
    ACADEMIC = "academic"
    SYSTEM = "system"


class AuthLevel(str, Enum):
    AUTO = "auto"
    CONFIRMATION = "confirmation_required"
    DISABLED = "disabled"


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: ToolCategory
    auth_level: AuthLevel
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)
    timeout_seconds: int = 30
    reversible: bool = True
    max_per_session: int | None = None
    example: str = ""
    handler: Callable[..., Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "auth_level": self.auth_level.value,
            "required_params": self.required_params,
            "optional_params": self.optional_params,
            "timeout_seconds": self.timeout_seconds,
            "reversible": self.reversible,
            "max_per_session": self.max_per_session,
            "example": self.example,
        }


class ToolRegistry:
    """Central registry of all available tools.

    Tools are registered at startup. Each tool declares its
    authorization requirements and safety metadata.
    """

    _instance: ToolRegistry | None = None

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._register_defaults()

    @classmethod
    def get_instance(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self, category: ToolCategory | None = None) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def list_all(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tools.values()]

    def _register_defaults(self) -> None:
        self.register(ToolDefinition(
            name="read_pdf",
            description="Read and extract content from uploaded PDF documents",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            required_params=["document_id"],
            example="Read my DBMS notes PDF",
        ))
        self.register(ToolDefinition(
            name="search_documents",
            description="Semantic search across all uploaded documents",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            required_params=["query"],
            example="Find all mentions of normalisation in my notes",
        ))
        self.register(ToolDefinition(
            name="get_assignment",
            description="Retrieve assignment details from workspace",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            required_params=["assignment_id"],
            example="Show me my DBMS assignment details",
        ))
        self.register(ToolDefinition(
            name="list_assignments",
            description="List all assignments with optional filters",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            optional_params=["status", "subject_id"],
            example="What assignments do I have due this week?",
        ))
        self.register(ToolDefinition(
            name="get_schedule",
            description="Retrieve current schedule and deadlines",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            optional_params=["date_range"],
            example="Show my schedule for next week",
        ))
        self.register(ToolDefinition(
            name="create_assignment",
            description="Create a new assignment in workspace",
            category=ToolCategory.WRITING,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["title"],
            optional_params=["subject_id", "deadline", "description", "priority"],
            reversible=False,
            example="Create a DBMS assignment due next Friday",
        ))
        self.register(ToolDefinition(
            name="update_assignment",
            description="Update assignment details",
            category=ToolCategory.WRITING,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["assignment_id"],
            optional_params=["title", "deadline", "status", "priority"],
            example="Change my DBMS assignment deadline to next Monday",
        ))
        self.register(ToolDefinition(
            name="delete_assignment",
            description="Delete an assignment from workspace",
            category=ToolCategory.DESTRUCTIVE,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["assignment_id"],
            reversible=False,
            example="Delete my cancelled assignment",
        ))
        self.register(ToolDefinition(
            name="create_study_plan",
            description="Generate a study plan for upcoming exams or goals",
            category=ToolCategory.SCHEDULING,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["subject"],
            optional_params=["duration_days", "hours_per_day"],
            example="Create a 7-day study plan for DBMS",
        ))
        self.register(ToolDefinition(
            name="add_to_planner",
            description="Add a task or event to the planner",
            category=ToolCategory.SCHEDULING,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["title"],
            optional_params=["date", "time", "duration_minutes"],
            example="Add study session for DBMS tomorrow at 2pm",
        ))
        self.register(ToolDefinition(
            name="start_pomodoro",
            description="Start a Pomodoro timer for focused work",
            category=ToolCategory.SCHEDULING,
            auth_level=AuthLevel.AUTO,
            optional_params=["duration_minutes", "task_description"],
            example="Start a 25-minute Pomodoro for DBMS revision",
        ))
        self.register(ToolDefinition(
            name="web_search",
            description="Search the web for current information",
            category=ToolCategory.WEB,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["query"],
            timeout_seconds=15,
            example="Search for latest React 19 features",
        ))
        self.register(ToolDefinition(
            name="fetch_url",
            description="Fetch and extract content from a URL",
            category=ToolCategory.WEB,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["url"],
            timeout_seconds=30,
            example="Fetch content from this article about TypeScript 6",
        ))
        self.register(ToolDefinition(
            name="save_opportunity",
            description="Save an internship/job opportunity to goals",
            category=ToolCategory.ACADEMIC,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["title", "company"],
            optional_params=["url", "deadline", "description"],
            reversible=False,
            example="Save this Google internship to my opportunities",
        ))
        self.register(ToolDefinition(
            name="create_flashcards",
            description="Generate flashcards from document content",
            category=ToolCategory.ACADEMIC,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["topic"],
            optional_params=["document_id", "count"],
            example="Create 10 flashcards on normalisation from my notes",
        ))
        self.register(ToolDefinition(
            name="create_quiz",
            description="Generate quiz questions from document content",
            category=ToolCategory.ACADEMIC,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["topic"],
            optional_params=["document_id", "count", "difficulty"],
            example="Create a 5-question quiz on OS memory management",
        ))
        self.register(ToolDefinition(
            name="compose_email",
            description="Draft an email for the student",
            category=ToolCategory.COMMUNICATION,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["recipient", "subject"],
            optional_params=["body", "attachments"],
            example="Compose an email to my professor about deadline extension",
        ))
        self.register(ToolDefinition(
            name="read_email",
            description="Read and summarize recent emails",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            optional_params=["from_address", "unread_only"],
            example="Show me recent unread emails",
        ))
        self.register(ToolDefinition(
            name="send_reminder",
            description="Create a reminder notification",
            category=ToolCategory.SYSTEM,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["message"],
            optional_params=["when"],
            example="Remind me to submit assignment tomorrow at 9am",
        ))
        self.register(ToolDefinition(
            name="delete_document",
            description="Delete an uploaded document and its associated data",
            category=ToolCategory.DESTRUCTIVE,
            auth_level=AuthLevel.CONFIRMATION,
            required_params=["document_id"],
            reversible=False,
            example="Delete my old physics notes",
        ))
        self.register(ToolDefinition(
            name="clear_conversation",
            description="Clear conversation history (memories retained)",
            category=ToolCategory.DESTRUCTIVE,
            auth_level=AuthLevel.CONFIRMATION,
            reversible=False,
            example="Clear our conversation history",
        ))
        self.register(ToolDefinition(
            name="study_scoring",
            description="View study points and streak",
            category=ToolCategory.READING,
            auth_level=AuthLevel.AUTO,
            example="How many points do I have today?",
        ))
