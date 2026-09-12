"""Unified Context Engine for Fixly AI.

Central pipeline that assembles relevant context before generation:

POST /ai/chat
→ IntentClassifier
→ ContextAssembly
→ local workspace context
→ RAG retrieval when needed
→ memory retrieval when relevant
→ recent conversation + summary
→ source authority resolution
→ bounded context
→ AIService generation
→ response + sources
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.services.intent_classifier import Intent, IntentClassifier
from app.services.memory_service import MemoryService
from app.services.rag_service import RAGService
from app.services.source_authority import SourceAuthority, SourceType
from app.services.summarization_service import SummarizationService

logger = get_logger(__name__)

# Context budget (tokens)
TOTAL_BUDGET = 4000
BUDGET_ALLOCATION = {
    "system": 500,
    "workspace": 800,
    "rag": 1200,
    "memory": 500,
    "conversation": 800,
    "response_reserve": 200,
}


class ContextEngine:
    """Assembles bounded context for AI generation.

    Determines what information is relevant to a user request
    and assembles it before generation.
    """

    def __init__(self) -> None:
        self.intent_classifier = IntentClassifier()
        self.memory_service = MemoryService()
        self.rag_service = RAGService()
        self.summarization_service = SummarizationService()

    async def assemble_context(
        self,
        user_id: str,
        message: str,
        workspace_data: dict[str, Any] | None = None,
        document_ids: list[str] | None = None,
        conversation_messages: list[dict[str, str]] | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Assemble context for an AI chat request.

        Returns:
            {
                "intent": Intent,
                "intent_details": {...},
                "sources": [...],
                "context_prompt": str,
                "source_authority": str,
                "budget_used": int,
                "budget_total": int,
                "citations": [...],
            }
        """
        workspace_data = workspace_data or {}
        document_ids = document_ids or []
        conversation_messages = conversation_messages or []

        # 1. Classify intent
        has_docs = len(document_ids) > 0
        intent_result = self.intent_classifier.classify(message, has_docs)
        intent = intent_result["intent"]

        # 2. Determine question type for source authority
        question_type = SourceAuthority.classify_question_type(intent, message)
        primary_source = SourceAuthority.get_primary(question_type)

        # 3. Gather context sources based on intent and authority
        sources = []
        citations = []
        budget_used = BUDGET_ALLOCATION["system"]  # System prompt always included

        # Workspace context (always partially included)
        workspace_budget = BUDGET_ALLOCATION["workspace"]
        workspace_ctx = self._build_workspace_context(workspace_data, workspace_budget)
        if workspace_ctx:
            sources.append({
                "type": "workspace",
                "content": workspace_ctx,
                "authority": SourceType.WORKSPACE.value,
            })
            budget_used += len(workspace_ctx.split())

        # RAG retrieval (when documents exist and query is document-related)
        if document_ids and intent in (
            Intent.DOCUMENT_QUERY,
            Intent.ASSIGNMENT_SOLVE,
            Intent.TUTORING,
        ):
            rag_budget = BUDGET_ALLOCATION["rag"]
            rag_result = await self._retrieve_rag(user_id, message, document_ids, rag_budget)
            if rag_result:
                sources.append({
                    "type": "rag",
                    "content": rag_result["context_prompt"],
                    "authority": SourceType.DOCUMENTS.value,
                    "citations": rag_result.get("sources", []),
                })
                citations.extend(rag_result.get("sources", []))
                budget_used += len(rag_result.get("context_prompt", "").split())

        # Memory retrieval (when relevant)
        if intent not in (Intent.SIMPLE_CHAT,):
            memory_budget = BUDGET_ALLOCATION["memory"]
            memory_ctx = self._retrieve_memory(user_id, message, memory_budget)
            if memory_ctx:
                sources.append({
                    "type": "memory",
                    "content": memory_ctx,
                    "authority": SourceType.MEMORY.value,
                })
                budget_used += len(memory_ctx.split())

        # Conversation context (recent + summary)
        conv_budget = BUDGET_ALLOCATION["conversation"]
        conv_ctx = self._build_conversation_context(
            user_id, conversation_id or "", conversation_messages, conv_budget
        )
        if conv_ctx:
            sources.append({
                "type": "conversation",
                "content": conv_ctx,
                "authority": "conversation",
            })
            budget_used += len(conv_ctx.split())

        # 4. Resolve source authority
        authority_info = SourceAuthority.resolve(question_type)
        authority_str = " → ".join(s.value for s in authority_info[:3])

        # 5. Build final context prompt
        context_prompt = self._compose_context(sources, message)

        return {
            "intent": intent,
            "intent_details": intent_result,
            "question_type": question_type,
            "primary_source": primary_source.value,
            "sources": sources,
            "context_prompt": context_prompt,
            "source_authority": authority_str,
            "budget_used": budget_used,
            "budget_total": TOTAL_BUDGET,
            "citations": citations,
        }

    def _build_workspace_context(
        self, workspace_data: dict[str, Any], budget: int
    ) -> str:
        """Build workspace context string within token budget."""
        parts = []
        if workspace_data.get("profile"):
            p = workspace_data["profile"]
            name = p.get("full_name", "Student")
            parts.append(f"Student: {name}")
        if workspace_data.get("subjects"):
            subj = ", ".join(s.get("name", "") for s in workspace_data["subjects"][:5])
            parts.append(f"Subjects: {subj}")
        if workspace_data.get("assignments"):
            assignments = workspace_data["assignments"][:3]
            for a in assignments:
                parts.append(f"Assignment: {a.get('title', '')} (due {a.get('deadline', '')})")
        if workspace_data.get("upcoming_deadlines"):
            for d in workspace_data["upcoming_deadlines"][:3]:
                parts.append(f"Deadline: {d}")

        context = "\n".join(parts)
        words = context.split()
        if len(words) > budget:
            context = " ".join(words[:budget])
        return context

    async def _retrieve_rag(
        self, user_id: str, query: str, document_ids: list[str], budget: int
    ) -> dict[str, Any] | None:
        """Retrieve relevant document chunks via RAG."""
        try:
            result = await self.rag_service.search_with_context(
                user_id, query, top_k=5
            )
            if result and result.get("chunks"):
                # Truncate to budget
                ctx = result["context_prompt"]
                words = ctx.split()
                if len(words) > budget:
                    ctx = " ".join(words[:budget])
                    result["context_prompt"] = ctx
                return result
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", e)
        return None

    def _retrieve_memory(self, user_id: str, query: str, budget: int) -> str:
        """Retrieve relevant memories."""
        try:
            return self.memory_service.build_memory_context(
                user_id, query, top_k=5, max_tokens=budget // 4
            )
        except Exception as e:
            logger.warning("Memory retrieval failed: %s", e)
            return ""

    def _build_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
        budget: int,
    ) -> str:
        """Build conversation context with summaries for older messages."""
        parts = []

        # Get summaries for older context
        if conversation_id:
            summary_ctx = self.summarization_service.build_summary_context(
                user_id, conversation_id, max_tokens=budget // 2
            )
            if summary_ctx:
                parts.append(f"[Earlier conversation]\n{summary_ctx}")

        # Add recent messages
        recent = messages[-6:] if len(messages) > 6 else messages
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            parts.append(f"{role}: {content}")

        context = "\n".join(parts)
        words = context.split()
        if len(words) > budget:
            context = " ".join(words[:budget])
        return context

    def _compose_context(self, sources: list[dict[str, Any]], query: str) -> str:
        """Compose final context prompt from all sources."""
        parts = []
        for source in sources:
            stype = source.get("type", "unknown")
            content = source.get("content", "")
            if content:
                parts.append(f"[{stype.upper()}]\n{content}")
        parts.append(f"\n[USER QUERY]\n{query}")
        return "\n\n".join(parts)
