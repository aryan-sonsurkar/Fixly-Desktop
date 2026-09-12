"""Tool Handler Registration.

Wires all tool handlers to the ToolExecutor at application startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.services.tool_executor import ToolExecutor
from app.services.tool_handlers import (
    ToolHandlerContext,
    handle_clear_conversation,
    handle_compose_email,
    handle_create_assignment,
    handle_create_flashcards,
    handle_create_quiz,
    handle_create_study_plan,
    handle_delete_assignment,
    handle_delete_document,
    handle_fetch_url,
    handle_get_assignment,
    handle_get_schedule,
    handle_list_assignments,
    handle_read_email,
    handle_read_pdf,
    handle_save_opportunity,
    handle_search_documents,
    handle_send_reminder,
    handle_start_pomodoro,
    handle_study_scoring,
    handle_update_assignment,
    handle_web_search,
    handle_add_to_planner,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Maps tool_name -> handler function
HANDLER_MAP: dict[str, callable] = {
    "read_pdf": handle_read_pdf,
    "search_documents": handle_search_documents,
    "get_assignment": handle_get_assignment,
    "list_assignments": handle_list_assignments,
    "get_schedule": handle_get_schedule,
    "create_assignment": handle_create_assignment,
    "update_assignment": handle_update_assignment,
    "delete_assignment": handle_delete_assignment,
    "create_study_plan": handle_create_study_plan,
    "add_to_planner": handle_add_to_planner,
    "start_pomodoro": handle_start_pomodoro,
    "web_search": handle_web_search,
    "fetch_url": handle_fetch_url,
    "save_opportunity": handle_save_opportunity,
    "create_flashcards": handle_create_flashcards,
    "create_quiz": handle_create_quiz,
    "compose_email": handle_compose_email,
    "read_email": handle_read_email,
    "send_reminder": handle_send_reminder,
    "delete_document": handle_delete_document,
    "clear_conversation": handle_clear_conversation,
    "study_scoring": handle_study_scoring,
}


def register_all_handlers(executor: ToolExecutor) -> int:
    """Register all tool handlers with the executor.

    Returns the number of handlers registered.
    """
    count = 0
    for tool_name, handler in HANDLER_MAP.items():
        executor.register_handler(tool_name, handler)
        count += 1
    logger.info("Registered %d tool handlers", count)
    return count
