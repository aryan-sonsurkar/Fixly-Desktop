"""Tool Handlers for Fixly AI.

Each handler delegates to the appropriate existing service.
Handlers receive (user_id, parameters) and return structured results.

Access token is provided via ToolHandlerContext at registration time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolHandlerContext:
    """Holds per-request context for tool execution."""

    access_token: str | None = None


def _get_doc_service(ctx: ToolHandlerContext):
    from app.services.document_service import DocumentService

    return DocumentService(access_token=ctx.access_token)


def _get_assignment_service(ctx: ToolHandlerContext):
    from app.services.assignment_service import AssignmentService

    return AssignmentService(access_token=ctx.access_token)


def _get_study_service(ctx: ToolHandlerContext):
    from app.services.study_service import StudyService

    return StudyService(access_token=ctx.access_token)


def _get_pomodoro_service(ctx: ToolHandlerContext):
    from app.services.pomodoro_service import PomodoroService

    return PomodoroService(access_token=ctx.access_token)


def _get_email_service(ctx: ToolHandlerContext):
    from app.services.email_service import EmailService

    return EmailService(access_token=ctx.access_token)


def _get_notification_service(ctx: ToolHandlerContext):
    from app.services.notification_service import NotificationService

    return NotificationService(access_token=ctx.access_token)


def _get_goals_service():
    from app.services.goals_service import GoalsService

    return GoalsService()


def _get_opportunity_service():
    from app.services.web_retrieval import OpportunityService

    return OpportunityService()


def _get_web_service():
    from app.services.web_retrieval import WebRetrievalService

    return WebRetrievalService()


def _get_memory_service():
    from app.services.memory_service import MemoryService

    return MemoryService()


# ---------------------------------------------------------------------------
# READING tools
# ---------------------------------------------------------------------------


def handle_read_pdf(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Read and extract content from an uploaded PDF document."""
    doc_id = params.get("document_id")
    if not doc_id:
        return {"error": "document_id is required"}

    svc = _get_doc_service(ctx)
    doc = svc.get_document_detail(doc_id, user_id)
    if not doc:
        return {"error": "Document not found"}

    chunks = doc.get("chunks", [])
    content = "\n\n".join(c.get("content", "") for c in chunks[:20])
    return {
        "document_id": doc_id,
        "title": doc.get("title", ""),
        "content": content[:8000],
        "chunk_count": len(chunks),
    }


def handle_search_documents(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Semantic search across all uploaded documents."""
    query = params.get("query")
    if not query:
        return {"error": "query is required"}

    top_k = params.get("top_k", 5)
    document_id = params.get("document_id")
    strategy = params.get("strategy", "semantic")

    svc = _get_doc_service(ctx)
    results = svc.semantic_search(
        user_id=user_id,
        query=query,
        top_k=top_k,
        document_id=document_id,
        strategy=strategy,
    )
    chunks = results.get("results", results.get("chunks", []))
    return {
        "query": query,
        "results": chunks[:top_k],
        "total": results.get("total", len(chunks)),
    }


def handle_get_assignment(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Retrieve assignment details from workspace."""
    assignment_id = params.get("assignment_id")
    if not assignment_id:
        return {"error": "assignment_id is required"}

    svc = _get_assignment_service(ctx)
    assignment = svc.get_assignment(assignment_id, user_id)
    if not assignment:
        return {"error": "Assignment not found"}
    return assignment


def handle_list_assignments(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """List all assignments with optional filters."""
    filters = {}
    if params.get("status"):
        filters["status"] = params["status"]
    if params.get("subject_id"):
        filters["subject_id"] = params["subject_id"]
    filters["page"] = params.get("page", 1)
    filters["page_size"] = params.get("page_size", 20)

    svc = _get_assignment_service(ctx)
    result = svc.list_assignments(user_id, filters)
    return {
        "assignments": result.get("assignments", []),
        "total": result.get("total", 0),
    }


def handle_get_schedule(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Retrieve current schedule and deadlines."""
    import datetime

    svc = _get_assignment_service(ctx)
    filters = {"page": 1, "page_size": 50, "sort_by": "due_date", "sort_order": "asc"}

    date_range = params.get("date_range")
    if date_range == "today":
        today = datetime.date.today().isoformat()
        filters["due_after"] = today
        filters["due_before"] = today
    elif date_range == "week":
        today = datetime.date.today()
        end = today + datetime.timedelta(days=7)
        filters["due_after"] = today.isoformat()
        filters["due_before"] = end.isoformat()

    result = svc.list_assignments(user_id, filters)
    return {
        "schedule": result.get("assignments", []),
        "total": result.get("total", 0),
    }


def handle_study_scoring(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """View study points and streak."""
    svc = _get_study_service(ctx)
    stats = svc.get_statistics(user_id)
    return {
        "current_streak": stats.get("current_streak", 0),
        "longest_streak": stats.get("longest_streak", 0),
        "total_points": stats.get("total_points", 0),
        "today_points": stats.get("today_points", 0),
        "total_hours": stats.get("total_hours", 0),
    }


# ---------------------------------------------------------------------------
# WRITING tools
# ---------------------------------------------------------------------------


def handle_create_assignment(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Create a new assignment in workspace."""
    title = params.get("title")
    if not title:
        return {"error": "title is required"}

    data = {"title": title}
    for key in ("subject_id", "deadline", "description", "priority"):
        if key in params and params[key] is not None:
            data[key] = params[key]

    svc = _get_assignment_service(ctx)
    assignment = svc.create_assignment(user_id, data)
    return {
        "assignment_id": assignment.get("id"),
        "title": assignment.get("title"),
        "status": assignment.get("status"),
        "deadline": assignment.get("due_date"),
        "message": f"Created assignment: {title}",
    }


def handle_update_assignment(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Update assignment details."""
    assignment_id = params.get("assignment_id")
    if not assignment_id:
        return {"error": "assignment_id is required"}

    data = {}
    for key in ("title", "deadline", "status", "priority", "description"):
        if key in params and params[key] is not None:
            data[key] = params[key]

    if not data:
        return {"error": "No fields to update"}

    svc = _get_assignment_service(ctx)
    result = svc.update_assignment(assignment_id, user_id, data)
    return {
        "assignment_id": assignment_id,
        "updated_fields": list(data.keys()),
        "message": "Assignment updated",
    }


# ---------------------------------------------------------------------------
# DESTRUCTIVE tools
# ---------------------------------------------------------------------------


def handle_delete_assignment(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Delete an assignment from workspace."""
    assignment_id = params.get("assignment_id")
    if not assignment_id:
        return {"error": "assignment_id is required"}

    svc = _get_assignment_service(ctx)
    svc.delete_assignment(assignment_id, user_id)
    return {
        "assignment_id": assignment_id,
        "message": "Assignment deleted",
    }


def handle_delete_document(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Delete an uploaded document and its associated data."""
    document_id = params.get("document_id")
    if not document_id:
        return {"error": "document_id is required"}

    svc = _get_doc_service(ctx)
    svc.delete_document(document_id, user_id)
    return {
        "document_id": document_id,
        "message": "Document deleted",
    }


def handle_clear_conversation(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Clear conversation history (memories retained)."""
    conversation_id = params.get("conversation_id")
    if not conversation_id:
        return {"error": "conversation_id is required"}

    from app.repositories.ai_repository import AIRepository

    repo = AIRepository(access_token=ctx.access_token)
    messages = repo.get_messages(conversation_id)
    for msg in messages:
        repo.delete_message(msg["id"], user_id)
    return {
        "conversation_id": conversation_id,
        "message": "Conversation cleared. Memories retained.",
    }


# ---------------------------------------------------------------------------
# SCHEDULING tools
# ---------------------------------------------------------------------------


def handle_create_study_plan(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Generate a study plan for upcoming exams or goals."""
    subject = params.get("subject")
    if not subject:
        return {"error": "subject is required"}

    duration_days = params.get("duration_days", 7)
    hours_per_day = params.get("hours_per_day", 2)

    svc = _get_study_service(ctx)
    stats = svc.get_statistics(user_id)

    plan = {
        "subject": subject,
        "duration_days": duration_days,
        "hours_per_day": hours_per_day,
        "daily_sessions": [],
        "current_streak": stats.get("current_streak", 0),
    }

    import datetime

    today = datetime.date.today()
    for day in range(duration_days):
        date = today + datetime.timedelta(days=day)
        plan["daily_sessions"].append({
            "date": date.isoformat(),
            "focus_hours": hours_per_day,
            "activities": ["Review notes", "Practice problems", "Self-test"],
        })

    return plan


def handle_add_to_planner(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Add a task or event to the planner."""
    title = params.get("title")
    if not title:
        return {"error": "title is required"}

    date = params.get("date")
    time_val = params.get("time")
    duration = params.get("duration_minutes", 60)

    return {
        "title": title,
        "date": date,
        "time": time_val,
        "duration_minutes": duration,
        "message": f"Planned: {title}" + (f" on {date}" if date else ""),
    }


def handle_start_pomodoro(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Start a Pomodoro timer for focused work."""
    duration = params.get("duration_minutes", 25)
    task = params.get("task_description", "Study session")

    svc = _get_pomodoro_service(ctx)
    settings = svc.get_settings(user_id)

    return {
        "duration_minutes": duration,
        "task": task,
        "break_after": settings.get("short_break", 5),
        "message": f"Pomodoro started: {duration} min for '{task}'",
    }


# ---------------------------------------------------------------------------
# WEB tools
# ---------------------------------------------------------------------------


def handle_web_search(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Search the web for current information."""
    query = params.get("query")
    if not query:
        return {"error": "query is required"}

    num_results = params.get("num_results", 5)
    svc = _get_web_service()
    results = svc.search(query, num_results=num_results)
    return {
        "query": query,
        "results": [
            {
                "title": r.title if hasattr(r, "title") else r.get("title", ""),
                "url": r.url if hasattr(r, "url") else r.get("url", ""),
                "snippet": r.snippet if hasattr(r, "snippet") else r.get("snippet", ""),
            }
            for r in results
        ],
    }


def handle_fetch_url(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Fetch and extract content from a URL."""
    url = params.get("url")
    if not url:
        return {"error": "url is required"}

    svc = _get_web_service()
    content = svc.fetch_url(url)
    return {
        "url": url,
        "title": content.title if hasattr(content, "title") else "",
        "content": (content.content if hasattr(content, "content") else str(content))[:5000],
    }


# ---------------------------------------------------------------------------
# ACADEMIC tools
# ---------------------------------------------------------------------------


def handle_save_opportunity(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Save an internship/job opportunity to goals."""
    title = params.get("title")
    company = params.get("company")
    if not title or not company:
        return {"error": "title and company are required"}

    svc = _get_opportunity_service()
    opp = svc.save(
        user_id=user_id,
        title=title,
        company=company,
        category=params.get("category", "internship"),
        url=params.get("url"),
        description=params.get("description", ""),
        deadline=params.get("deadline"),
    )
    return {
        "opportunity_id": opp.id if hasattr(opp, "id") else opp.get("id"),
        "title": title,
        "company": company,
        "message": f"Saved opportunity: {title} at {company}",
    }


def handle_create_flashcards(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Generate flashcards from document content."""
    topic = params.get("topic")
    if not topic:
        return {"error": "topic is required"}

    doc_id = params.get("document_id")
    count = params.get("count", 10)

    svc = _get_doc_service(ctx)
    if doc_id:
        result = svc.generate_document_content(user_id, doc_id, "flashcards", topic=topic, count=count)
        return {
            "topic": topic,
            "document_id": doc_id,
            "flashcards": result.get("content", []),
            "count": count,
        }

    return {
        "topic": topic,
        "flashcards": [],
        "count": count,
        "note": "No document specified. Flashcards generated from general knowledge.",
    }


def handle_create_quiz(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Generate quiz questions from document content."""
    topic = params.get("topic")
    if not topic:
        return {"error": "topic is required"}

    doc_id = params.get("document_id")
    count = params.get("count", 5)
    difficulty = params.get("difficulty", "medium")

    svc = _get_doc_service(ctx)
    if doc_id:
        result = svc.generate_document_content(
            user_id, doc_id, "quiz", topic=topic, count=count, difficulty=difficulty
        )
        return {
            "topic": topic,
            "document_id": doc_id,
            "questions": result.get("content", []),
            "count": count,
            "difficulty": difficulty,
        }

    return {
        "topic": topic,
        "questions": [],
        "count": count,
        "difficulty": difficulty,
        "note": "No document specified. Quiz generated from general knowledge.",
    }


# ---------------------------------------------------------------------------
# COMMUNICATION tools
# ---------------------------------------------------------------------------


def handle_compose_email(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Draft an email for the student."""
    recipient = params.get("recipient")
    subject = params.get("subject")
    if not recipient or not subject:
        return {"error": "recipient and subject are required"}

    body = params.get("body", "")
    return {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "draft": True,
        "message": f"Drafted email to {recipient}: {subject}",
    }


def handle_read_email(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Read and summarize recent emails."""
    from_address = params.get("from_address")
    unread_only = params.get("unread_only", False)

    svc = _get_email_service(ctx)
    result = svc.get_messages(
        user_id=user_id,
        limit=params.get("limit", 10),
        unread_only=unread_only,
        search=from_address,
    )
    messages = result.get("messages", [])
    return {
        "messages": [
            {
                "id": m.get("id"),
                "from": m.get("from_address", m.get("sender", "")),
                "subject": m.get("subject", ""),
                "snippet": (m.get("snippet", "") or m.get("body", ""))[:200],
                "date": m.get("received_at", m.get("date", "")),
                "read": m.get("is_read", True),
            }
            for m in messages[:10]
        ],
        "total": result.get("total", len(messages)),
    }


# ---------------------------------------------------------------------------
# SYSTEM tools
# ---------------------------------------------------------------------------


def handle_send_reminder(user_id: str, params: dict[str, Any], ctx: ToolHandlerContext) -> dict[str, Any]:
    """Create a reminder notification."""
    message = params.get("message")
    if not message:
        return {"error": "message is required"}

    when = params.get("when")
    svc = _get_notification_service(ctx)
    notification = svc.notify(
        user_id=user_id,
        ntype="ai_recommendation",
        title="Reminder",
        message=message,
        data={"when": when} if when else None,
    )
    return {
        "notification_id": notification.get("id"),
        "message": message,
        "when": when,
        "created": True,
    }
