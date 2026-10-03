"""Authoritative academic context (P0.2).

Single place that assembles persisted student academic state for AI
consumption. Reads ONLY existing Supabase-backed repositories — no new
tables, no migrations, no parallel stores.

Scope rules (PRD v2.0 P0.2):
- Subject == Course identity (existing subjects table).
- Topics/syllabus are DERIVED from stored material (chunk headings,
  assignment titles), never invented.
- Every method is user-scoped, bounded, and safe on missing data.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.subject_repository import SubjectRepository

logger = get_logger(__name__)

MAX_SUBJECTS = 20
MAX_ASSIGNMENTS = 10
MAX_DOCUMENTS = 5
MAX_DEADLINES = 20
MAX_HEADING_DOCS = 3
MAX_HEADINGS_PER_DOC = 20

# Words too generic to count as course abbreviations. Without this,
# everyday words ("test", "notes", "help") would subsequence-match
# unrelated course names and poison detection.
_DETECT_STOPWORDS = frozenset({
    "test", "tests", "exam", "exams", "quiz", "quizzes", "study",
    "studying", "homework", "assignment", "assignments", "class",
    "course", "courses", "lecture", "lectures", "notes", "note",
    "chapter", "chapters", "help", "please", "what", "should",
    "tomorrow", "tonight", "today", "prepare", "preparing",
    "revise", "revision", "practice", "learn", "learning",
    "understand", "explaining", "explain", "topic", "topics",
    "subject", "subjects", "material", "materials", "syllabus",
    "portion", "portions", "important", "question", "questions",
    "answer", "answers", "doubt", "doubts", "session", "part",
    "parts", "unit", "units", "module", "modules", "first",
    "make", "have", "with", "from", "that", "this", "and",
})


def _normalize_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9 ]", "", value.lower())
    return re.sub(r"\s+", " ", slug).strip()


def _is_subsequence(query: str, name: str) -> bool:
    """True when every query character appears in name in order.

    Covers abbreviations ("phy" → "philosophy"), acronyms ("dms" →
    "database management systems") and plain substrings, generically.
    """
    q = re.sub(r"[^a-z]", "", query.lower())
    n = re.sub(r"[^a-z]", "", name.lower())
    if not q or not n:
        return False
    it = iter(n)
    return all(ch in it for ch in q)


class AcademicContextService:
    """Deterministic, bounded academic context over persisted entities."""

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.subject_repo = SubjectRepository(access_token=access_token)
        self.assignment_repo = AssignmentRepository(access_token=access_token)
        self.document_repo = DocumentRepository(access_token=access_token)

    # ── subject resolution ────────────────────────────────

    async def resolve_course(
        self, user_id: str, subject_ref: str,
        subjects: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Resolve a user-supplied course reference to an owned subject.

        Returns a discriminated result — never guesses on ambiguity:
        {"status": "found", "subject": {...}}
        {"status": "ambiguous", "candidates": [...]}
        {"status": "missing", "query": ...}

        `subjects` optionally reuses an already-fetched user-scoped
        subject list (same request) to avoid a redundant query.
        """
        ref = (subject_ref or "").strip()
        if not ref:
            return {"status": "missing", "query": subject_ref}

        if subjects is None:
            try:
                subjects = await self.subject_repo.list_subjects(user_id)
            except Exception as e:
                logger.warning("Course resolution failed listing subjects: %s", e)
                return {"status": "missing", "query": subject_ref}

        # 1. Direct ID (validates ownership implicitly: list is user-scoped).
        try:
            sid = str(UUID(ref))
        except (ValueError, AttributeError, TypeError):
            sid = ""
        if sid:
            hit = next((s for s in subjects if str(s.get("id")) == sid), None)
            if hit:
                return {"status": "found", "subject": self._trim_subject(hit)}
            return {"status": "missing", "query": subject_ref}

        # 2. Exact normalized name.
        norm = _normalize_name(ref)
        exact = [s for s in subjects if _normalize_name(str(s.get("name", ""))) == norm]
        if len(exact) == 1:
            return {"status": "found", "subject": self._trim_subject(exact[0])}

        # 3. Abbreviation / acronym / substring, as a letter subsequence.
        # Zero or multiple hits resolve to missing / explicit ambiguity —
        # the resolver never guesses between candidates.
        hits = [
            s for s in subjects
            if _is_subsequence(norm, str(s.get("name", "")))
        ]
        # Deduplicate while preserving order.
        seen: dict[str, dict[str, Any]] = {}
        for s in exact + hits:
            seen[str(s.get("id"))] = s
        matches = list(seen.values())
        if len(matches) == 1:
            return {"status": "found", "subject": self._trim_subject(matches[0])}
        if matches:
            return {
                "status": "ambiguous",
                "candidates": [self._trim_subject(s) for s in matches],
            }
        return {"status": "missing", "query": subject_ref}

    @staticmethod
    def _trim_subject(subject: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(subject.get("id", "")),
            "name": str(subject.get("name", "")),
        }

    async def detect_course_mention(
        self, user_id: str, message: str,
        subjects: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Detect whether a chat message names one of the user's courses.

        Three tiers, strongest wins (strong tiers combine; the
        abbreviation tier only applies when no strong signal exists):
        1. full subject name appears in the message;
        2. a standalone token equals the name initials ("dsa" → "Data
           Structures and Algorithms" is NOT matched — initials must be
           exact, so "C" or "art" inside other words never trigger);
        3. a non-generic message word is a letter-subsequence of the
           name ("dbms" → "Database Management Systems").
        Multiple subjects at the winning tier resolve to explicit
        ambiguity — never a guess. Generic messages return missing and
        inject nothing.
        """
        text = _normalize_name(message or "")
        if not text:
            return {"status": "missing"}
        if subjects is None:
            try:
                subjects = await self.subject_repo.list_subjects(user_id)
            except Exception as e:
                logger.warning("Course-mention detection failed listing subjects: %s", e)
                return {"status": "missing"}
        strong_hits: list[dict[str, Any]] = []
        abbr_hits: list[dict[str, Any]] = []
        words = text.split()
        for subject in subjects:
            name = _normalize_name(str(subject.get("name", "")))
            if not name:
                continue
            if name in text:
                strong_hits.append(subject)
                continue
            initials = "".join(w[0] for w in name.split() if w)
            if len(initials) >= 3 and re.search(rf"\b{re.escape(initials)}\b", text):
                strong_hits.append(subject)
                continue
            spaceless = re.sub(r"[^a-z]", "", name)
            if len(spaceless) >= 3 and any(
                len(w) >= 3 and w not in _DETECT_STOPWORDS
                and _is_subsequence(w, spaceless)
                for w in words
            ):
                abbr_hits.append(subject)
        pool = strong_hits if strong_hits else abbr_hits
        seen: dict[str, dict[str, Any]] = {}
        for subject in pool:
            seen[str(subject.get("id"))] = subject
        unique = list(seen.values())
        if len(unique) == 1:
            return {"status": "found", "subject": self._trim_subject(unique[0])}
        if unique:
            return {
                "status": "ambiguous",
                "candidates": [self._trim_subject(s) for s in unique],
            }
        return {"status": "missing"}

    @staticmethod
    def format_course_context_block(course_ctx: dict[str, Any], max_chars: int = 1200) -> str:
        """Compact model-facing rendering of ONE resolved course.

        Strict contract (P0.2 Loop 9):
        - single [COURSE] ... [/COURSE] envelope, sections in fixed order:
          Course / Upcoming / Assignments / Documents / Topics / Grounding.
        - only data retrieved for the resolved course; empty sections are
          omitted, never invented; fully-empty context stays honest.
        - no user ids, no database ids, no unrelated subjects, no history,
          no unbounded document text (titles/names/dates only).
        - deterministic: input order preserved, duplicates dropped by
          (title, due) / (id or name) keeping first occurrence.
        - total length capped; truncation keeps the closing marker intact.
        """
        subject = course_ctx.get("subject") or {}
        name = str(subject.get("name", "Unknown"))
        lines = ["[COURSE]", f"Course: {name}"]

        dates = [str(d) for d in (course_ctx.get("upcoming_dates") or []) if d]
        if dates:
            lines.append("Upcoming:")
            lines.extend(f"- {d}" for d in dates[:5])

        seen_assignments: set[tuple[str, str]] = set()
        assignment_lines: list[str] = []
        for assignment in (course_ctx.get("assignments") or [])[:6]:
            title = str(assignment.get("title", "")).strip()
            if not title:
                continue
            due = str(assignment.get("due_date") or "") or "no due date"
            key = (title, due)
            if key in seen_assignments:
                continue
            seen_assignments.add(key)
            assignment_lines.append(
                f"- {title} (due {due}, {assignment.get('priority', 'medium')})"
            )
        if assignment_lines:
            lines.append("Assignments:")
            lines.extend(assignment_lines)

        seen_docs: set[str] = set()
        doc_lines: list[str] = []
        for doc in (course_ctx.get("documents") or [])[:5]:
            doc_name = str(doc.get("name", "")).strip()
            if not doc_name:
                continue
            key = str(doc.get("id") or doc_name)
            if key in seen_docs:
                continue
            seen_docs.add(key)
            doc_lines.append(f"- {doc_name} ({doc.get('pages', 0)} pages)")
        if doc_lines:
            lines.append("Documents:")
            lines.extend(doc_lines)

        topics = [str(t).strip() for t in (course_ctx.get("topic_signals") or []) if str(t).strip()]
        if topics:
            lines.append("Topics:")
            lines.append("- " + ", ".join(topics[:10]))

        if len(lines) == 2:
            lines.append("(No linked assignments, documents, topics, or dates stored.)")
        lines.append(
            f"Grounding: facts about {name} must come from this block only; "
            "if a fact is absent, say so. Prefer the dated items above over "
            "generic advice. Never claim to have read a document not listed here."
        )
        lines.append("[/COURSE]")
        block = "\n".join(lines)
        if len(block) > max_chars:
            closer = "\n[/COURSE]"
            block = block[: max_chars - len(closer)].rstrip() + closer
        return block

    # ── course context ────────────────────────────────────

    async def get_course_context(
        self, user_id: str, subject_ref: str,
        max_assignments: int = MAX_ASSIGNMENTS,
        max_documents: int = MAX_DOCUMENTS,
        subjects: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Bounded context for one course: identity, assignments, documents,
        dates, and topic signals derived from stored material."""
        resolved = await self.resolve_course(user_id, subject_ref, subjects=subjects)
        if resolved["status"] != "found":
            return {
                "subject": None,
                "resolution": resolved,
                "assignments": [],
                "documents": [],
                "upcoming_dates": [],
                "topic_signals": [],
                "truncated": False,
            }

        subject = resolved["subject"]
        subject_id = subject["id"]
        try:
            assignment_rows, _ = await self.assignment_repo.list_assignments(
                user_id, page=1, page_size=50, sort_by="due_date", sort_order="asc",
                filters={"subject_id": subject_id},
            )
        except Exception as e:
            logger.warning("Course assignments fetch failed: %s", e)
            assignment_rows = []
        try:
            doc_rows, _ = await self.document_repo.list_documents(
                user_id, page=1, page_size=max_documents, subject_id=subject_id,
            )
        except Exception as e:
            logger.warning("Course documents fetch failed: %s", e)
            doc_rows = []

        assignments = [
            {
                "title": str(a.get("title", "")),
                "status": str(a.get("status", "")),
                "priority": str(a.get("priority", "medium")),
                "due_date": str(a.get("due_date", "") or "")[:10] or None,
            }
            for a in assignment_rows[:max_assignments]
        ]
        documents = [
            {
                "id": str(d.get("id", "")),
                "name": str(d.get("original_name", "Untitled")),
                "pages": d.get("page_count", 0),
                "status": str(d.get("status", "")),
            }
            for d in doc_rows[:max_documents]
        ]
        upcoming_dates = sorted({
            a["due_date"] for a in assignments if a["due_date"]
        })
        topic_signals = await self._topic_signals(user_id, [d["id"] for d in documents[:MAX_HEADING_DOCS]])
        truncated = len(assignment_rows) > max_assignments or len(doc_rows) > max_documents
        return {
            "subject": subject,
            "resolution": {"status": "found"},
            "assignments": assignments,
            "documents": documents,
            "upcoming_dates": upcoming_dates,
            "topic_signals": topic_signals,
            "truncated": truncated,
        }

    async def _topic_signals(self, user_id: str, document_ids: list[str]) -> list[str]:
        """Headings from stored chunks (max 3 docs × 20 headings). Derived, never invented."""
        signals: list[str] = []
        for document_id in document_ids[:MAX_HEADING_DOCS]:
            try:
                chunks = await self.document_repo.get_chunks(document_id, user_id)
            except Exception as e:
                logger.warning("Topic signal fetch failed for %s: %s", document_id, e)
                continue
            for chunk in chunks:
                heading = str(chunk.get("heading") or "").strip()
                if heading and heading not in signals:
                    signals.append(heading)
                if len(signals) >= MAX_HEADING_DOCS * MAX_HEADINGS_PER_DOC:
                    break
            if len(signals) >= MAX_HEADING_DOCS * MAX_HEADINGS_PER_DOC:
                break
        return signals[:MAX_HEADING_DOCS * MAX_HEADINGS_PER_DOC]

    # ── deadlines ─────────────────────────────────────────

    async def get_upcoming_deadlines(
        self, user_id: str, days: int = 14, limit: int = MAX_DEADLINES,
    ) -> dict[str, Any]:
        """Authoritative deadline source: assignments with due dates."""
        from datetime import timedelta
        try:
            rows, _ = await self.assignment_repo.list_assignments(
                user_id, page=1, page_size=100, sort_by="due_date", sort_order="asc",
                filters={"status": ["pending", "in_progress"]},
            )
        except Exception as e:
            logger.warning("Deadline fetch failed: %s", e)
            return {"deadlines": [], "truncated": False}
        try:
            subjects = await self.subject_repo.list_subjects(user_id)
            names = {str(s.get("id")): str(s.get("name", "")) for s in subjects}
        except Exception:
            names = {}
        today = datetime.now(timezone.utc).date()
        horizon = today + timedelta(days=max(0, days))
        out: list[dict[str, Any]] = []
        for a in rows:
            due_raw = str(a.get("due_date", "") or "")[:10]
            if not due_raw:
                continue
            try:
                due = datetime.fromisoformat(due_raw).date()
            except ValueError:
                continue
            if due > horizon:
                continue
            out.append({
                "title": str(a.get("title", "")),
                "subject": names.get(str(a.get("subject_id") or ""), ""),
                "due_date": due_raw,
                "overdue": due < today,
                "priority": str(a.get("priority", "medium")),
                "estimated_minutes": a.get("estimated_study_time"),
            })
            if len(out) >= limit:
                break
        return {"deadlines": out, "truncated": len(out) >= limit}

    # ── student overview ──────────────────────────────────

    async def get_student_context(
        self, user_id: str,
        max_subjects: int = MAX_SUBJECTS,
        max_assignments: int = MAX_ASSIGNMENTS,
        max_documents: int = MAX_DOCUMENTS,
    ) -> dict[str, Any]:
        """Bounded whole-student snapshot for relevance decisions."""
        try:
            subjects = await self.subject_repo.list_subjects(user_id)
        except Exception as e:
            logger.warning("Student context subjects failed: %s", e)
            subjects = []
        try:
            assignment_rows, _ = await self.assignment_repo.list_assignments(
                user_id, page=1, page_size=50, sort_by="due_date", sort_order="asc",
                filters={"status": ["pending", "in_progress"]},
            )
        except Exception as e:
            logger.warning("Student context assignments failed: %s", e)
            assignment_rows = []
        try:
            doc_rows, _ = await self.document_repo.list_documents(
                user_id, page=1, page_size=max_documents,
            )
        except Exception as e:
            logger.warning("Student context documents failed: %s", e)
            doc_rows = []
        deadlines = await self.get_upcoming_deadlines(user_id, days=14, limit=10)
        names = {str(s.get("id")): str(s.get("name", "")) for s in subjects}
        return {
            "subjects": [
                {"id": str(s.get("id", "")), "name": str(s.get("name", ""))}
                for s in subjects[:max_subjects]
            ],
            "assignment_counts": {
                "pending_or_active": len(assignment_rows),
            },
            "upcoming": [
                {
                    "title": str(a.get("title", "")),
                    "subject": names.get(str(a.get("subject_id") or ""), ""),
                    "due_date": str(a.get("due_date", "") or "")[:10] or None,
                    "priority": str(a.get("priority", "medium")),
                }
                for a in assignment_rows[:max_assignments]
            ],
            "documents": [
                {
                    "id": str(d.get("id", "")),
                    "name": str(d.get("original_name", "Untitled")),
                    "subject_id": str(d.get("subject_id") or "") or None,
                }
                for d in doc_rows[:max_documents]
            ],
            "deadlines": deadlines["deadlines"],
            "truncated": (
                len(subjects) > max_subjects
                or len(assignment_rows) > max_assignments
                or len(doc_rows) > max_documents
                or deadlines["truncated"]
            ),
        }
