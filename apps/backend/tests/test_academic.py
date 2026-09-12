"""Tests for Phase 6: Academic Profile + Weakness Detection."""

from __future__ import annotations

import pytest

from app.services.academic_profile import (
    AcademicProfile,
    AcademicProfileService,
    SubjectPerformance,
)
from app.services.weakness_detector import WeaknessDetector, WeaknessSignal


# ── Academic Profile Tests ───────────────────────────────────────────


class TestAcademicProfileService:
    """Tests for academic profile management."""

    def setup_method(self):
        self.service = AcademicProfileService(":memory:")

    def teardown_method(self):
        self.service.close()

    def test_get_profile_creates_new(self):
        profile = self.service.get_profile("u1")
        assert profile.user_id == "u1"
        assert profile.subjects == {}

    def test_get_profile_existing(self):
        self.service.update_score("u1", "DBMS", 85)
        profile = self.service.get_profile("u1")
        assert "DBMS" in profile.subjects

    def test_update_score(self):
        self.service.update_score("u1", "DBMS", 85)
        self.service.update_score("u1", "DBMS", 90)
        profile = self.service.get_profile("u1")
        assert profile.subjects["DBMS"].scores == [85, 90]

    def test_average_score(self):
        perf = SubjectPerformance(subject="DBMS", scores=[80, 90, 70])
        assert perf.average_score == 80.0

    def test_trend_improving(self):
        perf = SubjectPerformance(subject="DBMS", scores=[60, 70, 80])
        assert perf.trend == "improving"

    def test_trend_declining(self):
        perf = SubjectPerformance(subject="DBMS", scores=[90, 80, 70])
        assert perf.trend == "declining"

    def test_trend_stable(self):
        perf = SubjectPerformance(subject="DBMS", scores=[80, 82, 78])
        assert perf.trend == "stable"

    def test_add_weak_topic(self):
        self.service.add_weak_topic("u1", "DBMS", "normalisation")
        profile = self.service.get_profile("u1")
        assert "normalisation" in profile.subjects["DBMS"].weak_topics

    def test_add_strong_topic(self):
        self.service.add_strong_topic("u1", "DBMS", "SQL queries")
        profile = self.service.get_profile("u1")
        assert "SQL queries" in profile.subjects["DBMS"].strong_topics

    def test_study_hours(self):
        self.service.update_study_hours("u1", "DBMS", 2.5)
        self.service.update_study_hours("u1", "DBMS", 1.0)
        profile = self.service.get_profile("u1")
        assert profile.subjects["DBMS"].total_study_hours == 3.5

    def test_weak_subjects(self):
        self.service.update_score("u1", "DBMS", 45)
        self.service.update_score("u1", "OS", 85)
        weak = self.service.get_weak_subjects("u1", threshold=60)
        assert "DBMS" in weak
        assert "OS" not in weak

    def test_strong_subjects(self):
        self.service.update_score("u1", "DBMS", 95)
        strong = self.service.get_strong_subjects("u1", threshold=80)
        assert "DBMS" in strong

    def test_study_recommendations(self):
        self.service.update_score("u1", "DBMS", 45)
        self.service.add_weak_topic("u1", "DBMS", "normalisation")
        recs = self.service.get_study_recommendations("u1")
        assert len(recs) >= 1
        assert recs[0]["subject"] == "DBMS"
        assert recs[0]["priority"] == "high"

    def test_profile_persists(self):
        self.service.update_score("u1", "DBMS", 85)
        profile = self.service.get_profile("u1")
        assert profile.subjects["DBMS"].scores == [85]

    def test_user_isolation(self):
        self.service.update_score("u1", "DBMS", 85)
        self.service.update_score("u2", "OS", 90)
        p1 = self.service.get_profile("u1")
        p2 = self.service.get_profile("u2")
        assert "DBMS" in p1.subjects
        assert "DBMS" not in p2.subjects

    def test_to_dict(self):
        self.service.update_score("u1", "DBMS", 85)
        profile = self.service.get_profile("u1")
        d = profile.to_dict()
        assert d["user_id"] == "u1"
        assert "DBMS" in d["subjects"]


# ── Weakness Detector Tests ──────────────────────────────────────────


class TestWeaknessDetector:
    """Tests for weakness detection."""

    def setup_method(self):
        self.service = AcademicProfileService(":memory:")
        self.detector = WeaknessDetector(self.service)

    def teardown_method(self):
        self.service.close()

    def test_detect_empty_profile(self):
        signals = self.detector.detect("u1")
        assert signals == []

    def test_detect_low_scores(self):
        self.service.update_score("u1", "DBMS", 45)
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "low_score" for s in signals)

    def test_detect_declining_trend(self):
        for score in [90, 80, 70]:
            self.service.update_score("u1", "DBMS", score)
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "declining_trend" for s in signals)

    def test_detect_no_practice(self):
        self.service.update_score("u1", "DBMS", 85)
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "no_practice" for s in signals)

    def test_detect_declared_weaknesses(self):
        self.service.set_weaknesses("u1", ["pointers", "recursion"])
        signals = self.detector.detect("u1")
        assert any(s.signal_type == "knowledge_gap" for s in signals)

    def test_severity_high(self):
        self.service.update_score("u1", "DBMS", 30)
        signals = self.detector.detect("u1")
        low_score = [s for s in signals if s.signal_type == "low_score"]
        assert low_score[0].severity == "high"

    def test_severity_medium(self):
        self.service.update_score("u1", "DBMS", 50)
        signals = self.detector.detect("u1")
        low_score = [s for s in signals if s.signal_type == "low_score"]
        assert low_score[0].severity == "medium"

    def test_priority_topics(self):
        self.service.update_score("u1", "DBMS", 40)
        self.service.update_score("u1", "OS", 50)
        topics = self.detector.get_priority_topics("u1", limit=2)
        assert len(topics) == 2

    def test_subject_health(self):
        self.service.update_score("u1", "DBMS", 85)
        self.service.update_study_hours("u1", "DBMS", 5)
        health = self.detector.get_subject_health("u1")
        assert "DBMS" in health
        assert health["DBMS"]["score"] > 0

    def test_recommendations_exist(self):
        self.service.update_score("u1", "DBMS", 45)
        recs = self.service.get_study_recommendations("u1")
        assert len(recs) >= 1
