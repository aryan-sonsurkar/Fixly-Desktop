"""Experimental Focus Companion ranking (sidecar, additive only).

Deterministic, LLM-free selection of ONE next action from the student's
real persisted state. Reuses AcademicContextService exclusively — no second
academic-context system, no new tables, no writes, no schedule generation.

Ranking contract (documented, unit-locked):
1. Overdue items first — lateness always dominates.
2. Without a time window: earliest due date, then priority
   (urgent > high > medium > low), then shortest estimate, then title.
3. With a time window: items fitting the window rank ahead of items that
   do not (a fitting non-overdue item beats a non-fitting one, but never
   an overdue one); within each group, earliest due date, then priority,
   then shortest estimate, then title.
4. With a time window where NOTHING fits: shortest estimate wins (capped
   to the window), so the student still gets the smallest useful slice.
5. Title alphabetical is the final deterministic tiebreak everywhere.
Dismissed keys are skipped for the top pick. Suggested minutes cap at the
given window and default to 15 when unknown.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.services.academic_context import AcademicContextService

logger = get_logger(__name__)

_PRIORITY_WEIGHT = {"urgent": 40, "high": 30, "medium": 20, "low": 10}
_DEFAULT_MINUTES = 15


def _parse_date(value: str | None) -> Any:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def rank_candidates(
    candidates: list[dict[str, Any]],
    available_minutes: int | None = None,
    exclude_keys: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Pure deterministic ranking over candidate dicts.

    Each candidate: {key, title, subject, due_date (YYYY-MM-DD|None),
    overdue (bool), priority, estimated_minutes (int|None)}.
    Returns candidates sorted best-first with score metadata attached.
    """
    excluded = set(exclude_keys or [])
    today = datetime.now(timezone.utc).date()
    scored: list[tuple[tuple, dict[str, Any]]] = []
    for cand in candidates:
        key = str(cand.get("key", ""))
        if not key or key in excluded:
            continue
        due = _parse_date(cand.get("due_date"))
        overdue = bool(cand.get("overdue")) or (due is not None and due < today)
        days_until = (due - today).days if due is not None else 10**6
        priority = str(cand.get("priority", "medium")).lower()
        est = cand.get("estimated_minutes")
        try:
            est_int = int(est) if est is not None else None
        except (TypeError, ValueError):
            est_int = None
        fits = (
            available_minutes is None
            or est_int is None
            or est_int <= available_minutes
        )
        urgency = max(0, 30 - days_until) * 10 if days_until < 10**6 else 0
        est_sort = est_int if est_int is not None else 10**6
        entry = {
            **cand,
            "key": key,
            "overdue": overdue,
            "priority": priority,
            "estimated_minutes": est_int,
            "fits_window": fits,
        }
        scored.append((overdue, fits, urgency,
                       _PRIORITY_WEIGHT.get(priority, 20),
                       est_sort,
                       str(entry.get("title", "")), entry))
    if available_minutes is not None and scored:
        any_fits = any(item[1] for item in scored)
    else:
        any_fits = True
    if available_minutes is None or any_fits:
        scored.sort(key=lambda item: (
            not item[0], not item[1], -item[2], -item[3], item[4], item[5],
        ))
    else:
        # Window given but nothing fits: shortest estimate wins (capped
        # downstream), keeping overdue dominance. Urgency still breaks ties.
        scored.sort(key=lambda item: (
            not item[0], item[4], -item[2], -item[3], item[5],
        ))
    return [entry for *_, entry in scored]


def to_action(ranked: dict[str, Any], available_minutes: int | None,
               kind: str = "assignment") -> dict[str, Any]:
    est = ranked.get("estimated_minutes")
    suggested = est if isinstance(est, int) and est > 0 else _DEFAULT_MINUTES
    if available_minutes is not None:
        suggested = max(1, min(suggested, available_minutes))
    return {
        "kind": kind,
        "key": ranked["key"],
        "title": str(ranked.get("title", "")),
        "subject": str(ranked.get("subject", "")),
        "due_date": ranked.get("due_date"),
        "overdue": bool(ranked.get("overdue", False)),
        "priority": ranked.get("priority", "medium"),
        "suggested_minutes": suggested,
        "reason": str(ranked.get("reason", "")),
        "document_id": ranked.get("document_id"),
        "document_name": ranked.get("document_name"),
    }


class CompanionService:
    """Assembles next-action candidates from persisted academic state."""

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.academic = AcademicContextService(access_token=access_token)

    async def _candidates(self, user_id: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Raw candidates + subject-name lookup. Read-only, bounded."""
        try:
            snapshot = await self.academic.get_student_context(user_id)
        except Exception as e:
            logger.warning("Companion snapshot failed: %s", e)
            return [], {}
        subjects = {s.get("id", ""): s.get("name", "")
                    for s in snapshot.get("subjects", [])}
        candidates: list[dict[str, Any]] = []
        for item in snapshot.get("upcoming", []):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            candidates.append({
                "key": f"assignment:{title}:{item.get('due_date') or ''}",
                "title": title,
                "subject": str(item.get("subject", "")),
                "due_date": item.get("due_date"),
                "overdue": False,
                "priority": item.get("priority", "medium"),
                "estimated_minutes": None,
                "reason": "",
            })
        for deadline in snapshot.get("deadlines", []):
            title = str(deadline.get("title", "")).strip()
            if not title:
                continue
            key = f"assignment:{title}:{deadline.get('due_date') or ''}"
            if any(c["key"] == key for c in candidates):
                for c in candidates:
                    if c["key"] == key:
                        c["overdue"] = bool(deadline.get("overdue", False))
                        if deadline.get("estimated_minutes") is not None:
                            try:
                                c["estimated_minutes"] = int(deadline["estimated_minutes"])
                            except (TypeError, ValueError):
                                pass
                continue
            candidates.append({
                "key": key,
                "title": title,
                "subject": str(deadline.get("subject", "")),
                "due_date": deadline.get("due_date"),
                "overdue": bool(deadline.get("overdue", False)),
                "priority": deadline.get("priority", "medium"),
                "estimated_minutes": deadline.get("estimated_minutes"),
                "reason": "",
            })
        for doc in snapshot.get("documents", []):
            name = str(doc.get("name", "")).strip()
            if not name:
                continue
            subject = subjects.get(str(doc.get("subject_id") or ""), "")
            candidates.append({
                "key": f"topic:{doc.get('id', '')}",
                "title": f"Review {name}",
                "subject": subject,
                "due_date": None,
                "overdue": False,
                "priority": "low",
                "estimated_minutes": 10,
                "reason": "",
                "document_id": str(doc.get("id", "")),
                "document_name": name,
            })
        return candidates, subjects

    @staticmethod
    def _explain(ranked: dict[str, Any], position: int) -> str:
        if ranked.get("overdue"):
            base = "It's already past due, so it buys back the most relief."
        elif ranked.get("due_date"):
            base = f"It's due {ranked['due_date']}, sooner than the rest."
        elif ranked.get("document_id"):
            base = "It's open material with no deadline pressure — a gentle start."
        else:
            base = "It's the smallest useful step available."
        if position > 0:
            base += " Next best after that."
        return base

    async def get_next_action(
        self,
        user_id: str,
        available_minutes: int | None = None,
        exclude_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """ONE action + up to 3 alternates, or an honest empty."""
        candidates, _ = await self._candidates(user_id)
        ranked = rank_candidates(candidates, available_minutes, exclude_keys)
        if not ranked:
            return {"action": None, "alternates": [],
                    "empty_reason": ("Nothing pending was found. Enjoy the clear plate "
                                     "— or add a subject to get started.")}
        top = dict(ranked[0])
        top["reason"] = self._explain(top, 0)
        alternates = []
        for i, cand in enumerate(ranked[1:4], start=1):
            c = dict(cand)
            c["reason"] = self._explain(c, i)
            kind = "assignment" if c["key"].startswith("assignment:") else "topic"
            alternates.append(to_action(c, available_minutes, kind))
        top_kind = "assignment" if top["key"].startswith("assignment:") else "topic"
        return {"action": to_action(top, available_minutes, top_kind),
                "alternates": alternates, "empty_reason": None}

    async def continue_session(
        self,
        user_id: str,
        current_key: str | None,
        available_minutes: int | None = None,
    ) -> dict[str, Any]:
        """Interruption recovery: re-validate the saved action, else move on.

        If the saved item is still pending, return it unchanged
        ("continue where you stopped"). Otherwise return the next best
        action — never a stale or completed item.
        """
        candidates, _ = await self._candidates(user_id)
        if current_key:
            live = [c for c in candidates if str(c.get("key", "")) == current_key]
            if live:
                ranked = rank_candidates(live, available_minutes, [])
                top = dict(ranked[0])
                top["reason"] = ("Still open — let's pick up where you stopped. "
                                 + self._explain(top, 0))
                kind = "assignment" if top["key"].startswith("assignment:") else "topic"
                return {"action": to_action(top, available_minutes, kind),
                        "alternates": [], "empty_reason": None,
                        "resumed": True}
        nxt = await self.get_next_action(user_id, available_minutes, [])
        nxt["resumed"] = False
        return nxt
