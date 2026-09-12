"""Tests for Phase 8: Web Retrieval + Opportunities."""

from __future__ import annotations

import pytest

from app.services.web_retrieval import (
    Opportunity,
    OpportunityService,
    WebContent,
    WebRetrievalService,
    WebSearchResult,
)


class TestOpportunityService:
    def setup_method(self):
        self.service = OpportunityService(":memory:")

    def teardown_method(self):
        self.service.close()

    def test_save_opportunity(self):
        opp = self.service.save("u1", "SWE Intern", "Google", category="internship",
                                url="https://careers.google.com", deadline="2026-12-01")
        assert opp.id.startswith("opp_")
        assert opp.title == "SWE Intern"
        assert opp.status == "saved"

    def test_list_saved(self):
        self.service.save("u1", "Intern 1", "Google")
        self.service.save("u1", "Intern 2", "Meta")
        self.service.save("u2", "Intern 3", "Apple")
        opps = self.service.list_saved("u1")
        assert len(opps) == 2

    def test_list_by_status(self):
        self.service.save("u1", "O1", "G1")
        o2 = self.service.save("u1", "O2", "G2")
        self.service.update_status("u1", o2.id, "applied")
        saved = self.service.list_saved("u1", status="saved")
        applied = self.service.list_saved("u1", status="applied")
        assert len(saved) == 1
        assert len(applied) == 1

    def test_update_status(self):
        opp = self.service.save("u1", "O1", "G1")
        updated = self.service.update_status("u1", opp.id, "applied")
        assert updated.status == "applied"

    def test_delete(self):
        opp = self.service.save("u1", "O1", "G1")
        assert self.service.delete("u1", opp.id) is True
        assert self.service.list_saved("u1") == []

    def test_user_isolation(self):
        self.service.save("u1", "O1", "G1")
        self.service.save("u2", "O2", "G2")
        assert len(self.service.list_saved("u1")) == 1
        assert len(self.service.list_saved("u2")) == 1

    def test_to_dict(self):
        opp = self.service.save("u1", "O1", "G1", category="scholarship")
        d = opp.to_dict()
        assert d["category"] == "scholarship"
        assert d["company"] == "G1"


class TestWebRetrievalService:
    def setup_method(self):
        self.service = WebRetrievalService()

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        results = await self.service.search("test query", num_results=3)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_fetch_url_returns_content(self):
        content = await self.service.fetch_url("https://example.com")
        assert content.url == "https://example.com"
        assert len(content.content) > 0

    def test_search_result_to_dict(self):
        r = WebSearchResult(title="T", url="U", snippet="S")
        assert r.title == "T"

    def test_web_content_fields(self):
        c = WebContent(url="u", title="t", content="c")
        assert c.url == "u"
