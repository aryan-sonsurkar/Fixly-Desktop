"""Workflow Engine for Fixly AI.

Orchestrates multi-step workflows. Each step calls a tool,
and the engine manages state transitions and error handling.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.services.tool_executor import ToolExecutor, ToolResult
from app.services.workflow_store import Workflow, WorkflowStep, WorkflowStore

logger = get_logger(__name__)

# Predefined workflow templates
WORKFLOW_TEMPLATES: dict[str, dict[str, Any]] = {
    "study_session": {
        "name": "Study Session",
        "description": "Start a focused study session with context",
        "steps": [
            {"tool": "list_assignments", "params": {"status": "pending"}},
            {"tool": "search_documents", "params": {"query": "{topic}"}},
            {"tool": "start_pomodoro", "params": {"duration_minutes": 25, "task_description": "Study {topic}"}},
        ],
    },
    "assignment_help": {
        "name": "Assignment Help",
        "description": "Get help with an assignment using uploaded notes",
        "steps": [
            {"tool": "get_assignment", "params": {"assignment_id": "{assignment_id}"}},
            {"tool": "search_documents", "params": {"query": "{assignment_topic}"}},
            {"tool": "create_flashcards", "params": {"topic": "{assignment_topic}"}},
        ],
    },
    "exam_prep": {
        "name": "Exam Preparation",
        "description": "Prepare for an exam with study plan, quizzes, and flashcards",
        "steps": [
            {"tool": "create_study_plan", "params": {"subject": "{subject}", "duration_days": 7}},
            {"tool": "search_documents", "params": {"query": "{subject}"}},
            {"tool": "create_quiz", "params": {"topic": "{subject}", "count": 10}},
            {"tool": "create_flashcards", "params": {"topic": "{subject}", "count": 20}},
        ],
    },
    "research_topic": {
        "name": "Research Topic",
        "description": "Research a topic with web search and document search",
        "steps": [
            {"tool": "search_documents", "params": {"query": "{topic}"}},
            {"tool": "web_search", "params": {"query": "{topic} latest research"}},
        ],
    },
}


class WorkflowEngine:
    """Orchestrates multi-step workflows with state management."""

    def __init__(
        self,
        store: WorkflowStore | None = None,
        executor: ToolExecutor | None = None,
    ) -> None:
        self.store = store or WorkflowStore()
        self.executor = executor or ToolExecutor()

    def create_workflow(
        self,
        user_id: str,
        name: str,
        steps: list[dict[str, str]],
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        """Create a new workflow with steps."""
        workflow = Workflow(
            id=f"wf_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            name=name,
            description=description,
            steps=[
                WorkflowStep(
                    id=f"step_{uuid.uuid4().hex[:8]}",
                    tool_name=s["tool"],
                    parameters=s.get("params", {}),
                )
                for s in steps
            ],
            metadata=metadata or {},
        )
        return self.store.create(workflow)

    def create_from_template(
        self,
        user_id: str,
        template_name: str,
        variables: dict[str, str] | None = None,
    ) -> Workflow:
        """Create a workflow from a predefined template."""
        template = WORKFLOW_TEMPLATES.get(template_name)
        if template is None:
            raise ValueError(f"Unknown template: {template_name}")

        variables = variables or {}
        steps = []
        for step_def in template["steps"]:
            params = {}
            for k, v in step_def["params"].items():
                if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                    var_name = v[1:-1]
                    params[k] = variables.get(var_name, v)
                else:
                    params[k] = v
            steps.append({"tool": step_def["tool"], "params": params})

        return self.create_workflow(
            user_id=user_id,
            name=template["name"],
            steps=steps,
            description=template["description"],
            metadata={"template": template_name},
        )

    def execute_next_step(self, workflow: Workflow) -> ToolResult | None:
        """Execute the next pending step in a workflow."""
        next_step = None
        for step in workflow.steps:
            if step.status == "pending":
                next_step = step
                break

        if next_step is None:
            workflow.status = "completed"
            self.store.update(workflow)
            return None

        next_step.status = "running"
        next_step.started_at = time.time()
        workflow.status = "running"
        self.store.update(workflow)

        result = self.executor.execute(
            next_step.tool_name,
            workflow.user_id,
            next_step.parameters,
        )

        if result.success:
            next_step.status = "completed"
            next_step.result = result.result
        else:
            next_step.status = "failed"
            next_step.error = result.error
            workflow.status = "failed"
            workflow.error = f"Step {next_step.id} failed: {result.error}"

        next_step.completed_at = time.time()
        self.store.update(workflow)
        return result

    def execute_all(self, workflow: Workflow) -> list[ToolResult]:
        """Execute all pending steps in a workflow."""
        results = []
        while True:
            result = self.execute_next_step(workflow)
            if result is None:
                break
            results.append(result)
            if not result.success:
                break
        return results

    def pause(self, workflow: Workflow) -> Workflow:
        workflow.status = "paused"
        return self.store.update(workflow)

    def resume(self, workflow: Workflow) -> Workflow:
        workflow.status = "pending"
        return self.store.update(workflow)

    def cancel(self, workflow: Workflow) -> Workflow:
        workflow.status = "failed"
        workflow.error = "Cancelled by user"
        for step in workflow.steps:
            if step.status == "pending":
                step.status = "skipped"
        return self.store.update(workflow)

    def get_status(self, workflow: Workflow) -> dict[str, Any]:
        completed = sum(1 for s in workflow.steps if s.status == "completed")
        total = len(workflow.steps)
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "progress": f"{completed}/{total}",
            "completed_steps": completed,
            "total_steps": total,
            "current_step": next(
                (s.to_dict() for s in workflow.steps if s.status == "running"),
                None,
            ),
        }

    def list_templates(self) -> list[dict[str, Any]]:
        return [
            {"name": k, "name_display": v["name"], "description": v["description"], "steps": len(v["steps"])}
            for k, v in WORKFLOW_TEMPLATES.items()
        ]
