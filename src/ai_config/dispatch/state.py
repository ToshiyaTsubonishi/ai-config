"""State definitions for the dispatch runtime graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass
class TaskStep:
    """A single development step to be delegated to a CLI agent."""

    step_id: str
    description: str
    agent: str  # "antigravity" | "gemini" | "codex"
    prompt: str
    depends_on: list[str] = field(default_factory=list)
    working_directory: str = "."
    timeout_seconds: int = 300


@dataclass
class StepResult:
    """Result of executing a single TaskStep."""

    step_id: str
    agent: str
    status: str  # "success" | "error" | "timeout" | "skipped"
    output: str = ""
    error: str = ""
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent": self.agent,
            "status": self.status,
            "output": self.output[:2000] if self.output else "",
            "error": self.error[:1000] if self.error else "",
            "retry_count": self.retry_count,
        }


class DispatchState(TypedDict, total=False):
    """LangGraph state for the dispatch runtime."""

    user_prompt: str
    working_directory: str
    repo_root: str

    # Plan
    plan: list[dict[str, Any]]  # serialized TaskStep list
    current_step: int
    total_steps: int
    approved_plan: dict[str, Any]
    tool_records: list[dict[str, Any]]

    # Agent availability
    available_agents: list[str]
    preferred_agents: list[str]  # user-specified via --agents

    # Execution
    step_results: list[dict[str, Any]]  # serialized StepResult list
    max_retries: int
    step_retry_count: int
    last_step_result: dict[str, Any] | None

    # Parallel dispatch
    parallel: bool

    # Session & context handoff
    session_id: str
    context_dir: str  # path to .dispatch/<session_id>/

    # Workflow
    workflow_name: str  # name of a predefined workflow

    # Control flow
    needs_replanning: bool
    replan_count: int
    max_replans: int
    replan_request: dict[str, Any] | None
    done: bool
    abort: bool
    dry_run: bool
    keep_context: bool  # if True, preserve .dispatch/ after finalization

    # Output
    final_report: str
    error: str | None
