"""Goals and Skills Management for Fixly AI.

Tracks student goals, skills, learning roadmap, and progress.
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
class Goal:
    id: str
    user_id: str
    title: str
    description: str
    category: str  # academic | career | personal
    target_date: str | None = None
    status: str = "active"  # active | completed | abandoned
    progress: float = 0.0  # 0-100
    milestones: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "title": self.title, "description": self.description,
            "category": self.category, "target_date": self.target_date,
            "status": self.status, "progress": self.progress,
            "milestones": self.milestones,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class Skill:
    id: str
    user_id: str
    name: str
    category: str  # programming | academic | soft_skill | tool
    level: str = "beginner"  # beginner | intermediate | advanced | expert
    evidence: list[str] = field(default_factory=list)
    last_practiced_at: float | None = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "name": self.name, "category": self.category,
            "level": self.level, "evidence": self.evidence,
            "last_practiced_at": self.last_practiced_at,
            "created_at": self.created_at,
        }


@dataclass
class RoadmapStep:
    id: str
    title: str
    description: str
    status: str = "pending"  # pending | in_progress | completed
    resources: list[str] = field(default_factory=list)
    estimated_hours: float = 0
    order: int = 0


@dataclass
class Roadmap:
    id: str
    user_id: str
    title: str
    goal_id: str | None = None
    steps: list[RoadmapStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id,
            "title": self.title, "goal_id": self.goal_id,
            "steps": [
                {"id": s.id, "title": s.title, "description": s.description,
                 "status": s.status, "resources": s.resources,
                 "estimated_hours": s.estimated_hours, "order": s.order}
                for s in self.steps
            ],
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


class GoalsService:
    """Manages goals, skills, and roadmaps with SQLite persistence."""

    def __init__(self, db_path: str | None = None) -> None:
        import sqlite3
        self._db_path = db_path or ":memory:"
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS ai_goals (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                description TEXT, category TEXT NOT NULL, target_date TEXT,
                status TEXT DEFAULT 'active', progress REAL DEFAULT 0,
                milestones TEXT DEFAULT '[]', created_at REAL, updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS ai_skills (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL,
                category TEXT NOT NULL, level TEXT DEFAULT 'beginner',
                evidence TEXT DEFAULT '[]', last_practiced_at REAL, created_at REAL
            );
            CREATE TABLE IF NOT EXISTS ai_roadmaps (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                goal_id TEXT, steps TEXT DEFAULT '[]', created_at REAL, updated_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_goals_user ON ai_goals(user_id);
            CREATE INDEX IF NOT EXISTS idx_skills_user ON ai_skills(user_id);
            CREATE INDEX IF NOT EXISTS idx_roadmaps_user ON ai_roadmaps(user_id);
        """)
        self._conn.commit()

    def create_goal(self, user_id: str, title: str, description: str = "",
                    category: str = "academic", target_date: str | None = None) -> Goal:
        goal = Goal(id=f"goal_{uuid.uuid4().hex[:12]}", user_id=user_id,
                    title=title, description=description, category=category,
                    target_date=target_date)
        self._conn.execute(
            "INSERT INTO ai_goals (id,user_id,title,description,category,target_date,status,progress,milestones,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (goal.id, goal.user_id, goal.title, goal.description, goal.category,
             goal.target_date, goal.status, goal.progress, json.dumps(goal.milestones),
             goal.created_at, goal.updated_at))
        self._conn.commit()
        return goal

    def get_goals(self, user_id: str, status: str | None = None) -> list[Goal]:
        if status:
            rows = self._conn.execute("SELECT * FROM ai_goals WHERE user_id=? AND status=?", (user_id, status)).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM ai_goals WHERE user_id=?", (user_id,)).fetchall()
        return [self._row_to_goal(r) for r in rows]

    def update_goal_progress(self, user_id: str, goal_id: str, progress: float) -> Goal | None:
        row = self._conn.execute("SELECT * FROM ai_goals WHERE id=? AND user_id=?", (goal_id, user_id)).fetchone()
        if not row:
            return None
        goal = self._row_to_goal(row)
        goal.progress = min(100, max(0, progress))
        if goal.progress >= 100:
            goal.status = "completed"
        goal.updated_at = time.time()
        self._conn.execute("UPDATE ai_goals SET progress=?, status=?, updated_at=? WHERE id=? AND user_id=?",
                           (goal.progress, goal.status, goal.updated_at, goal_id, user_id))
        self._conn.commit()
        return goal

    def add_skill(self, user_id: str, name: str, category: str = "academic",
                  level: str = "beginner") -> Skill:
        skill = Skill(id=f"skill_{uuid.uuid4().hex[:12]}", user_id=user_id,
                      name=name, category=category, level=level)
        self._conn.execute(
            "INSERT INTO ai_skills (id,user_id,name,category,level,evidence,last_practiced_at,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (skill.id, skill.user_id, skill.name, skill.category, skill.level,
             json.dumps(skill.evidence), skill.last_practiced_at, skill.created_at))
        self._conn.commit()
        return skill

    def get_skills(self, user_id: str, category: str | None = None) -> list[Skill]:
        if category:
            rows = self._conn.execute("SELECT * FROM ai_skills WHERE user_id=? AND category=?", (user_id, category)).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM ai_skills WHERE user_id=?", (user_id,)).fetchall()
        return [self._row_to_skill(r) for r in rows]

    def create_roadmap(self, user_id: str, title: str, steps: list[dict[str, Any]],
                       goal_id: str | None = None) -> Roadmap:
        roadmap = Roadmap(id=f"road_{uuid.uuid4().hex[:12]}", user_id=user_id,
                          title=title, goal_id=goal_id)
        for i, step_def in enumerate(steps):
            roadmap.steps.append(RoadmapStep(
                id=f"step_{uuid.uuid4().hex[:8]}",
                title=step_def.get("title", ""),
                description=step_def.get("description", ""),
                resources=step_def.get("resources", []),
                estimated_hours=step_def.get("estimated_hours", 0),
                order=i))
        self._conn.execute(
            "INSERT INTO ai_roadmaps (id,user_id,title,goal_id,steps,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (roadmap.id, roadmap.user_id, roadmap.title, roadmap.goal_id,
             json.dumps([{"id":s.id,"title":s.title,"description":s.description,"status":s.status,
                          "resources":s.resources,"estimated_hours":s.estimated_hours,"order":s.order}
                         for s in roadmap.steps]),
             roadmap.created_at, roadmap.updated_at))
        self._conn.commit()
        return roadmap

    def get_roadmaps(self, user_id: str) -> list[Roadmap]:
        rows = self._conn.execute("SELECT * FROM ai_roadmaps WHERE user_id=?", (user_id,)).fetchall()
        return [self._row_to_roadmap(r) for r in rows]

    def _row_to_goal(self, row: Any) -> Goal:
        return Goal(id=row["id"], user_id=row["user_id"], title=row["title"],
                    description=row["description"], category=row["category"],
                    target_date=row["target_date"], status=row["status"],
                    progress=row["progress"], milestones=json.loads(row["milestones"]),
                    created_at=row["created_at"], updated_at=row["updated_at"])

    def _row_to_skill(self, row: Any) -> Skill:
        return Skill(id=row["id"], user_id=row["user_id"], name=row["name"],
                     category=row["category"], level=row["level"],
                     evidence=json.loads(row["evidence"]),
                     last_practiced_at=row["last_practiced_at"],
                     created_at=row["created_at"])

    def _row_to_roadmap(self, row: Any) -> Roadmap:
        steps_data = json.loads(row["steps"])
        steps = [RoadmapStep(**s) for s in steps_data]
        return Roadmap(id=row["id"], user_id=row["user_id"], title=row["title"],
                       goal_id=row["goal_id"], steps=steps,
                       created_at=row["created_at"], updated_at=row["updated_at"])

    def close(self) -> None:
        self._conn.close()
