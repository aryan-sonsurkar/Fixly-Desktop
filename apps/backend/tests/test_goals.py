"""Tests for Phase 7: Goals + Skills + Roadmap."""

from __future__ import annotations

import pytest

from app.services.goals_service import GoalsService, Goal, Skill, Roadmap, RoadmapStep


class TestGoalsService:
    def setup_method(self):
        self.service = GoalsService(":memory:")

    def teardown_method(self):
        self.service.close()

    def test_create_goal(self):
        goal = self.service.create_goal("u1", "Learn Python", category="academic")
        assert goal.id.startswith("goal_")
        assert goal.title == "Learn Python"
        assert goal.status == "active"

    def test_get_goals(self):
        self.service.create_goal("u1", "Goal 1")
        self.service.create_goal("u1", "Goal 2")
        self.service.create_goal("u2", "Goal 3")
        goals = self.service.get_goals("u1")
        assert len(goals) == 2

    def test_get_goals_by_status(self):
        self.service.create_goal("u1", "G1")
        g2 = self.service.create_goal("u1", "G2")
        self.service.update_goal_progress("u1", g2.id, 100)
        active = self.service.get_goals("u1", status="active")
        completed = self.service.get_goals("u1", status="completed")
        assert len(active) == 1
        assert len(completed) == 1

    def test_update_goal_progress(self):
        goal = self.service.create_goal("u1", "Goal")
        updated = self.service.update_goal_progress("u1", goal.id, 50)
        assert updated.progress == 50
        assert updated.status == "active"

    def test_goal_auto_complete(self):
        goal = self.service.create_goal("u1", "Goal")
        updated = self.service.update_goal_progress("u1", goal.id, 100)
        assert updated.status == "completed"

    def test_add_skill(self):
        skill = self.service.add_skill("u1", "Python", category="programming")
        assert skill.id.startswith("skill_")
        assert skill.name == "Python"
        assert skill.level == "beginner"

    def test_get_skills(self):
        self.service.add_skill("u1", "Python", "programming")
        self.service.add_skill("u1", "DBMS", "academic")
        self.service.add_skill("u2", "Java", "programming")
        skills = self.service.get_skills("u1")
        assert len(skills) == 2

    def test_get_skills_by_category(self):
        self.service.add_skill("u1", "Python", "programming")
        self.service.add_skill("u1", "DBMS", "academic")
        prog = self.service.get_skills("u1", category="programming")
        assert len(prog) == 1

    def test_create_roadmap(self):
        roadmap = self.service.create_roadmap("u1", "Python Mastery", [
            {"title": "Learn basics", "estimated_hours": 10},
            {"title": "Build projects", "estimated_hours": 20},
        ])
        assert roadmap.id.startswith("road_")
        assert len(roadmap.steps) == 2
        assert roadmap.steps[0].order == 0

    def test_get_roadmaps(self):
        self.service.create_roadmap("u1", "Roadmap 1", [{"title": "Step 1"}])
        self.service.create_roadmap("u2", "Roadmap 2", [{"title": "Step 1"}])
        roadmaps = self.service.get_roadmaps("u1")
        assert len(roadmaps) == 1

    def test_user_isolation(self):
        self.service.create_goal("u1", "G1")
        self.service.create_goal("u2", "G2")
        assert len(self.service.get_goals("u1")) == 1
        assert len(self.service.get_goals("u2")) == 1

    def test_goal_to_dict(self):
        goal = self.service.create_goal("u1", "Test", description="desc", category="career")
        d = goal.to_dict()
        assert d["title"] == "Test"
        assert d["category"] == "career"

    def test_skill_to_dict(self):
        skill = self.service.add_skill("u1", "React", "programming", level="intermediate")
        d = skill.to_dict()
        assert d["level"] == "intermediate"

    def test_roadmap_to_dict(self):
        roadmap = self.service.create_roadmap("u1", "RM", [{"title": "S1"}])
        d = roadmap.to_dict()
        assert len(d["steps"]) == 1
