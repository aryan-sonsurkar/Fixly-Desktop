"""Web Retrieval and Opportunity Management for Fixly AI.

Provides web search, URL fetching, and opportunity tracking.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Opportunity:
    id: str
    user_id: str
    title: str
    company: str
    category: str  # internship | job | scholarship | competition
    url: str | None = None
    description: str = ""
    deadline: str | None = None
    status: str = "saved"  # saved | applied | expired | rejected
    notes: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "title": self.title, "company": self.company,
            "category": self.category, "url": self.url,
            "description": self.description, "deadline": self.deadline,
            "status": self.status, "notes": self.notes,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


@dataclass
class WebContent:
    url: str
    title: str
    content: str
    fetched_at: float = field(default_factory=time.time)


class WebRetrievalService:
    """Web search and content fetching."""

    def __init__(self) -> None:
        self._cache: dict[str, WebContent] = {}

    async def search(self, query: str, num_results: int = 5) -> list[WebSearchResult]:
        """Search the web. Returns cached/stub results in offline mode."""
        try:
            from app.services.web_search import web_search
            raw = await web_search(query, num_results=num_results)
            return [
                WebSearchResult(title=r.get("title", ""), url=r.get("url", ""),
                                snippet=r.get("snippet", ""))
                for r in raw
            ]
        except Exception as e:
            logger.warning("Web search failed: %s", e)
            return [WebSearchResult(
                title=f"Search: {query}",
                url="",
                snippet=f"Web search unavailable. Try again later.",
                source="offline",
            )]

    async def fetch_url(self, url: str) -> WebContent:
        """Fetch and extract content from a URL."""
        if url in self._cache:
            return self._cache[url]
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.text[:5000]
                result = WebContent(url=url, title=url, content=content)
                self._cache[url] = result
                return result
        except Exception as e:
            logger.warning("URL fetch failed for %s: %s", url, e)
            return WebContent(url=url, title=url, content=f"Fetch failed: {e}")


class OpportunityService:
    """Manages saved opportunities."""

    def __init__(self, db_path: str | None = None) -> None:
        import sqlite3
        self._db_path = db_path or ":memory:"
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS ai_opportunities (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                company TEXT NOT NULL, category TEXT NOT NULL, url TEXT,
                description TEXT, deadline TEXT, status TEXT DEFAULT 'saved',
                notes TEXT, created_at REAL, updated_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_opp_user ON ai_opportunities(user_id);
        """)
        self._conn.commit()

    def save(self, user_id: str, title: str, company: str,
             category: str = "internship", url: str | None = None,
             description: str = "", deadline: str | None = None) -> Opportunity:
        opp = Opportunity(id=f"opp_{uuid.uuid4().hex[:12]}", user_id=user_id,
                          title=title, company=company, category=category,
                          url=url, description=description, deadline=deadline)
        self._conn.execute(
            "INSERT INTO ai_opportunities (id,user_id,title,company,category,url,description,deadline,status,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (opp.id, opp.user_id, opp.title, opp.company, opp.category,
             opp.url, opp.description, opp.deadline, opp.status, opp.notes,
             opp.created_at, opp.updated_at))
        self._conn.commit()
        return opp

    def list_saved(self, user_id: str, status: str | None = None) -> list[Opportunity]:
        if status:
            rows = self._conn.execute("SELECT * FROM ai_opportunities WHERE user_id=? AND status=?", (user_id, status)).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM ai_opportunities WHERE user_id=?", (user_id,)).fetchall()
        return [self._row_to_opp(r) for r in rows]

    def update_status(self, user_id: str, opp_id: str, status: str) -> Opportunity | None:
        row = self._conn.execute("SELECT * FROM ai_opportunities WHERE id=? AND user_id=?", (opp_id, user_id)).fetchone()
        if not row:
            return None
        opp = self._row_to_opp(row)
        opp.status = status
        opp.updated_at = time.time()
        self._conn.execute("UPDATE ai_opportunities SET status=?, updated_at=? WHERE id=? AND user_id=?",
                           (status, opp.updated_at, opp_id, user_id))
        self._conn.commit()
        return opp

    def delete(self, user_id: str, opp_id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM ai_opportunities WHERE id=? AND user_id=?", (opp_id, user_id))
        self._conn.commit()
        return cursor.rowcount > 0

    def _row_to_opp(self, row: Any) -> Opportunity:
        return Opportunity(id=row["id"], user_id=row["user_id"], title=row["title"],
                           company=row["company"], category=row["category"],
                           url=row["url"], description=row["description"],
                           deadline=row["deadline"], status=row["status"],
                           notes=row["notes"], created_at=row["created_at"],
                           updated_at=row["updated_at"])

    def close(self) -> None:
        self._conn.close()
