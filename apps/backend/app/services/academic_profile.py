"""Academic Profile for Fixly AI.

Tracks student's academic context: subjects, scores, strengths,
weaknesses, and learning patterns.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SubjectPerformance:
    subject: str
    scores: list[float] = field(default_factory=list)
    total_study_hours: float = 0.0
    last_studied_at: float | None = None
    weak_topics: list[str] = field(default_factory=list)
    strong_topics: list[str] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def trend(self) -> str:
        if len(self.scores) < 2:
            return "insufficient_data"
        recent = self.scores[-3:]
        if len(recent) < 2:
            return "insufficient_data"
        first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        if second_half > first_half + 5:
            return "improving"
        elif second_half < first_half - 5:
            return "declining"
        return "stable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "scores": self.scores,
            "average_score": self.average_score,
            "trend": self.trend,
            "total_study_hours": self.total_study_hours,
            "weak_topics": self.weak_topics,
            "strong_topics": self.strong_topics,
        }


@dataclass
class AcademicProfile:
    user_id: str
    subjects: dict[str, SubjectPerformance] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    study_patterns: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "subjects": {k: v.to_dict() for k, v in self.subjects.items()},
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "goals": self.goals,
            "study_patterns": self.study_patterns,
            "updated_at": self.updated_at,
        }


class AcademicProfileService:
    """Manages academic profiles with SQLite persistence."""

    def __init__(self, db_path: str | None = None) -> None:
        import sqlite3
        self._db_path = db_path or ":memory:"
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS academic_profiles (
                user_id TEXT PRIMARY KEY,
                subjects TEXT NOT NULL DEFAULT '{}',
                strengths TEXT NOT NULL DEFAULT '[]',
                weaknesses TEXT NOT NULL DEFAULT '[]',
                goals TEXT NOT NULL DEFAULT '[]',
                study_patterns TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)
        self._conn.commit()

    def get_profile(self, user_id: str) -> AcademicProfile:
        row = self._conn.execute(
            "SELECT * FROM academic_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return self._row_to_profile(row)
        now = time.time()
        profile = AcademicProfile(user_id=user_id, created_at=now, updated_at=now)
        self._save(profile)
        return profile

    def update_score(self, user_id: str, subject: str, score: float) -> AcademicProfile:
        profile = self.get_profile(user_id)
        if subject not in profile.subjects:
            profile.subjects[subject] = SubjectPerformance(subject=subject)
        profile.subjects[subject].scores.append(score)
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def add_weak_topic(self, user_id: str, subject: str, topic: str) -> AcademicProfile:
        profile = self.get_profile(user_id)
        if subject not in profile.subjects:
            profile.subjects[subject] = SubjectPerformance(subject=subject)
        if topic not in profile.subjects[subject].weak_topics:
            profile.subjects[subject].weak_topics.append(topic)
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def add_strong_topic(self, user_id: str, subject: str, topic: str) -> AcademicProfile:
        profile = self.get_profile(user_id)
        if subject not in profile.subjects:
            profile.subjects[subject] = SubjectPerformance(subject=subject)
        if topic not in profile.subjects[subject].strong_topics:
            profile.subjects[subject].strong_topics.append(topic)
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def update_study_hours(self, user_id: str, subject: str, hours: float) -> AcademicProfile:
        profile = self.get_profile(user_id)
        if subject not in profile.subjects:
            profile.subjects[subject] = SubjectPerformance(subject=subject)
        profile.subjects[subject].total_study_hours += hours
        profile.subjects[subject].last_studied_at = time.time()
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def set_weaknesses(self, user_id: str, weaknesses: list[str]) -> AcademicProfile:
        profile = self.get_profile(user_id)
        profile.weaknesses = weaknesses
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def set_strengths(self, user_id: str, strengths: list[str]) -> AcademicProfile:
        profile = self.get_profile(user_id)
        profile.strengths = strengths
        profile.updated_at = time.time()
        self._save(profile)
        return profile

    def get_weak_subjects(self, user_id: str, threshold: float = 60.0) -> list[str]:
        profile = self.get_profile(user_id)
        return [
            subject for subject, perf in profile.subjects.items()
            if perf.average_score < threshold and perf.scores
        ]

    def get_strong_subjects(self, user_id: str, threshold: float = 80.0) -> list[str]:
        profile = self.get_profile(user_id)
        return [
            subject for subject, perf in profile.subjects.items()
            if perf.average_score >= threshold and perf.scores
        ]

    def get_study_recommendations(self, user_id: str) -> list[dict[str, Any]]:
        profile = self.get_profile(user_id)
        recommendations = []
        for subject, perf in profile.subjects.items():
            if perf.average_score < 60 and perf.scores:
                recommendations.append({
                    "subject": subject,
                    "reason": f"Low average score ({perf.average_score:.1f}%)",
                    "priority": "high",
                    "suggested_action": (
                        f"Review {', '.join(perf.weak_topics[:3])}"
                        if perf.weak_topics
                        else "General review needed"
                    ),
                })
            elif perf.trend == "declining":
                recommendations.append({
                    "subject": subject,
                    "reason": "Score trend is declining",
                    "priority": "medium",
                    "suggested_action": "Focus on recent weak areas",
                })
        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 3))

    def _save(self, profile: AcademicProfile) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO academic_profiles
               (user_id, subjects, strengths, weaknesses, goals, study_patterns, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (profile.user_id,
             json.dumps({k: v.to_dict() for k, v in profile.subjects.items()}),
             json.dumps(profile.strengths),
             json.dumps(profile.weaknesses),
             json.dumps(profile.goals),
             json.dumps(profile.study_patterns),
             profile.created_at,
             profile.updated_at),
        )
        self._conn.commit()

    def _row_to_profile(self, row: Any) -> AcademicProfile:
        subjects_data = json.loads(row["subjects"])
        subjects = {}
        for k, v in subjects_data.items():
            subjects[k] = SubjectPerformance(
                subject=v["subject"],
                scores=v.get("scores", []),
                total_study_hours=v.get("total_study_hours", 0),
                weak_topics=v.get("weak_topics", []),
                strong_topics=v.get("strong_topics", []),
            )
        return AcademicProfile(
            user_id=row["user_id"],
            subjects=subjects,
            strengths=json.loads(row["strengths"]),
            weaknesses=json.loads(row["weaknesses"]),
            goals=json.loads(row["goals"]),
            study_patterns=json.loads(row["study_patterns"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def close(self) -> None:
        self._conn.close()
