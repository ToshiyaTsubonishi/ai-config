from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from ai_config.dispatch.graph import create_dispatch_agent
from ai_config.orchestrator.plan_schema import OrchestrationPlan, PlanStep, ToolReference
from ai_config.registry.models import ToolRecord


def _skill_record(tmp_path: Path) -> ToolRecord:
    skill_path = tmp_path / "skills" / "shared" / "demo" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text("---\nname: demo\ndescription: demo skill\n---\n# Demo\n", encoding="utf-8")
    return ToolRecord(
        id="skill:demo",
        name="demo",
        description="demo skill",
        source_path=skill_path.relative_to(tmp_path).as_posix(),
        tool_kind="skill",
        metadata={"catalog_only": False, "executable": True},
        invoke={"backend": "skill_markdown", "command": skill_path.relative_to(tmp_path).as_posix(), "args": [], "timeout_ms": 1000, "env_keys": []},
    )


def _approved_plan() -> OrchestrationPlan:
    tool_ref = ToolReference(
        tool_id="skill:demo",
        tool_kind="skill",
        name="demo",
        source_path="skills/shared/demo/SKILL.md",
        selection_reason="approved",
        invoke_summary="skill_markdown: skills/shared/demo/SKILL.md",
        confidence=0.8,
    )
    return OrchestrationPlan(
        plan_id="plan-approved",
        revision=1,
        user_goal="Open the demo skill",
        assumptions=[],
        specialist_route="general",
        candidate_tools=[tool_ref],
        steps=[
            PlanStep(
                step_id="step-1",
                title="Open demo",
                purpose="Read the demo skill",
                inputs=["demo"],
                expected_output="content preview",
                tool_ref=tool_ref,
                depends_on=[],
                action="run",
                params={},
                working_directory=".",
            )
        ],
        approval_required=True,
        execution_notes="approved test",
        feasibility="full",
        notes="approved test",
    )


def test_dispatch_executes_approved_plan(tmp_path: Path) -> None:
    record = _skill_record(tmp_path)
    plan = _approved_plan()
    agent = create_dispatch_agent()

    result = agent.invoke(
        {
            "user_prompt": plan.user_goal,
            "working_directory": str(tmp_path),
            "repo_root": str(tmp_path),
            "approved_plan": plan.model_dump(),
            "tool_records": [record.to_dict()],
            "max_retries": 1,
            "max_replans": 0,
            "parallel": False,
            "dry_run": False,
            "step_results": [],
            "replan_count": 0,
            "replan_request": None,
            "done": False,
            "abort": False,
            "needs_replanning": False,
            "error": None,
            "final_report": "",
        }
    )

    assert result.get("done") is True
    assert "Approved Plan Execution" in result.get("final_report", "")
    assert "skill:demo" in result.get("final_report", "")
