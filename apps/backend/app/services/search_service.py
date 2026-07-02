from typing import Any

from app.core.logging import get_logger
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.subject_repository import SubjectRepository

logger = get_logger(__name__)


class SearchService:
    def __init__(self) -> None:
        self.assignment_repo = AssignmentRepository()
        self.email_repo = EmailRepository()
        self.document_repo = DocumentRepository()
        self.subject_repo = SubjectRepository()
        self.ai_repo = AIRepository()
        self.study_repo = StudyRepository()

    async def search_all(self, user_id: str, query: str, limit: int = 5) -> dict[str, Any]:
        q = query.lower().strip()
        if not q:
            return {"query": query, "results": []}

        results: list[dict[str, Any]] = []

        assignments = await self._search_assignments(user_id, q, limit)
        results.extend(assignments)

        subjects = await self._search_subjects(user_id, q, limit)
        results.extend(subjects)

        emails = await self._search_emails(user_id, q, limit)
        results.extend(emails)

        documents = await self._search_documents(user_id, q, limit)
        results.extend(documents)

        conversations = await self._search_conversations(user_id, q, limit)
        results.extend(conversations)

        notes = await self._search_notes(user_id, q, limit)
        results.extend(notes)

        results.sort(key=lambda r: r.get("_score", 0), reverse=True)
        results = results[:limit * 3]

        return {"query": query, "results": results, "total": len(results)}

    async def _search_assignments(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            items, _ = await self.assignment_repo.list_assignments(
                user_id, page=1, page_size=50,
            )
            matches = []
            for a in items:
                title = (a.get("title", "") or "").lower()
                desc = (a.get("description", "") or "").lower()
                if q in title or q in desc:
                    score = 10 if q in title else 5
                    matches.append({
                        "type": "assignment", "id": a.get("id", ""),
                        "title": a.get("title", ""), "subtitle": a.get("status", ""),
                        "url": f"/assignments/{a.get('id', '')}",
                        "_score": score,
                    })
            return matches[:limit]
        except Exception as e:
            logger.warning("Search assignments failed: %s", e)
            return []

    async def _search_subjects(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            subjects = await self.subject_repo.list_subjects(user_id)
            matches = []
            for s in subjects:
                name = (s.get("name", "") or "").lower()
                if q in name:
                    matches.append({
                        "type": "subject", "id": s.get("id", ""),
                        "title": s.get("name", ""), "subtitle": f"{s.get('credits', 0)} credits",
                        "url": f"/subjects/{s.get('id', '')}",
                        "_score": 8,
                    })
            return matches[:limit]
        except Exception as e:
            logger.warning("Search subjects failed: %s", e)
            return []

    async def _search_emails(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            msgs, _ = await self.email_repo.get_messages(user_id, limit=50, search=q)
            return [{
                "type": "email", "id": m.get("id", ""),
                "title": m.get("subject", "(No subject)"),
                "subtitle": m.get("from_name", m.get("from_email", "")),
                "url": f"/email/{m.get('id', '')}",
                "_score": 7,
            } for m in msgs[:limit]]
        except Exception as e:
            logger.warning("Search emails failed: %s", e)
            return []

    async def _search_documents(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            docs = await self.document_repo.get_recent_documents(user_id, limit=50)
            matches = []
            for d in docs:
                name = (d.get("original_name", "") or "").lower()
                if q in name:
                    matches.append({
                        "type": "document", "id": d.get("id", ""),
                        "title": d.get("original_name", ""),
                        "subtitle": d.get("doc_type", ""),
                        "url": f"/documents/{d.get('id', '')}",
                        "_score": 6,
                    })
            return matches[:limit]
        except Exception as e:
            logger.warning("Search documents failed: %s", e)
            return []

    async def _search_conversations(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            convs = await self.ai_repo.list_conversations(user_id)
            matches = []
            for c in convs:
                title = (c.get("title", "") or "").lower()
                if q in title:
                    matches.append({
                        "type": "conversation", "id": c.get("id", ""),
                        "title": c.get("title", ""),
                        "subtitle": "AI Conversation",
                        "url": f"/ai/{c.get('id', '')}",
                        "_score": 5,
                    })
            return matches[:limit]
        except Exception as e:
            logger.warning("Search conversations failed: %s", e)
            return []

    async def _search_notes(self, user_id: str, q: str, limit: int) -> list[dict[str, Any]]:
        try:
            notes = await self.ai_repo.list_conversations(user_id)
            matches = []
            for c in notes:
                msgs = await self.ai_repo.get_messages(c["id"])
                for m in msgs:
                    if m.get("role") == "assistant" and q in (m.get("content", "") or "").lower():
                        matches.append({
                            "type": "note", "id": m.get("id", ""),
                            "title": f"From: {c.get('title', 'Conversation')}",
                            "subtitle": (m.get("content", "") or "")[:100],
                            "url": f"/ai/{c.get('id', '')}",
                            "_score": 4,
                        })
                        break
            return matches[:limit]
        except Exception as e:
            logger.warning("Search notes failed: %s", e)
            return []
