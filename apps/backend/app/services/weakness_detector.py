"""Weakness Detector for Fixly AI.

Analyzes academic data to detect patterns of weakness:
- Low scores in specific topics
- Declining trends
- Insufficient practice
- Knowledge gaps from conversation patterns
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.services.academic_profile import AcademicProfile, AcademicProfileService

logger = get_logger(__name__)


@dataclass
class WeaknessSignal:
    subject: str
    topic: str
    signal_type: str  # low_score | declining_trend | no_practice | knowledge_gap
    severity: str  # high | medium | low
    evidence: str
    recommendation: str


class WeaknessDetector:
    """Detects academic weaknesses from multiple data sources."""

    def __init__(self, profile_service: AcademicProfileService) -> None:
        self.profile_service = profile_service

    def detect(self, user_id: str) -> list[WeaknessSignal]:
        """Detect all weaknesses for a user."""
        profile = self.profile_service.get_profile(user_id)
        signals = []
        signals.extend(self._check_low_scores(profile))
        signals.extend(self._check_declining_trends(profile))
        signals.extend(self._check_no_practice(profile))
        signals.extend(self._check_declared_weaknesses(profile))
        return sorted(signals, key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.severity, 3))

    def _check_low_scores(self, profile: AcademicProfile) -> list[WeaknessSignal]:
        signals = []
        for subject, perf in profile.subjects.items():
            if perf.scores and perf.average_score < 60:
                signals.append(WeaknessSignal(
                    subject=subject,
                    topic=subject,
                    signal_type="low_score",
                    severity="high" if perf.average_score < 40 else "medium",
                    evidence=f"Average score: {perf.average_score:.1f}%",
                    recommendation=f"Focus on fundamentals in {subject}",
                ))
        return signals

    def _check_declining_trends(self, profile: AcademicProfile) -> list[WeaknessSignal]:
        signals = []
        for subject, perf in profile.subjects.items():
            if perf.trend == "declining":
                signals.append(WeaknessSignal(
                    subject=subject,
                    topic=subject,
                    signal_type="declining_trend",
                    severity="medium",
                    evidence=f"Scores declining over last {len(perf.scores)} attempts",
                    recommendation=f"Review recent topics in {subject}",
                ))
        return signals

    def _check_no_practice(self, profile: AcademicProfile) -> list[WeaknessSignal]:
        signals = []
        for subject, perf in profile.subjects.items():
            if perf.total_study_hours < 2 and perf.scores:
                signals.append(WeaknessSignal(
                    subject=subject,
                    topic=subject,
                    signal_type="no_practice",
                    severity="low",
                    evidence=f"Only {perf.total_study_hours:.1f} hours studied",
                    recommendation=f"Increase practice time in {subject}",
                ))
        return signals

    def _check_declared_weaknesses(self, profile: AcademicProfile) -> list[WeaknessSignal]:
        signals = []
        for topic in profile.weaknesses:
            signals.append(WeaknessSignal(
                subject="general",
                topic=topic,
                signal_type="knowledge_gap",
                severity="medium",
                evidence="User-declared weakness",
                recommendation=f"Practice and review {topic}",
            ))
        return signals

    def get_priority_topics(self, user_id: str, limit: int = 5) -> list[str]:
        """Get the top priority topics to study."""
        signals = self.detect(user_id)
        seen = set()
        topics = []
        for signal in signals:
            if signal.topic not in seen:
                seen.add(signal.topic)
                topics.append(signal.topic)
                if len(topics) >= limit:
                    break
        return topics

    def get_subject_health(self, user_id: str) -> dict[str, dict[str, Any]]:
        """Get health score for each subject (0-100)."""
        profile = self.profile_service.get_profile(user_id)
        health = {}
        for subject, perf in profile.subjects.items():
            score = min(perf.average_score, 100)
            trend_bonus = 10 if perf.trend == "improving" else (-10 if perf.trend == "declining" else 0)
            practice_bonus = min(perf.total_study_hours * 2, 20)
            health_score = max(0, min(100, score + trend_bonus + practice_bonus))
            health[subject] = {
                "score": health_score,
                "average": perf.average_score,
                "trend": perf.trend,
                "study_hours": perf.total_study_hours,
                "weak_topics": perf.weak_topics,
                "strong_topics": perf.strong_topics,
            }
        return health
