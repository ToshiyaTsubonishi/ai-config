from __future__ import annotations

import json
from pathlib import Path

from ai_config.orchestrator.plan_schema import OrchestrationPlan, PlanStep, ToolReference
from ai_config.orchestrator.planner import OrchestrationPlanner
from ai_config.orchestrator.validator import validate_orchestration_plan
from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def _build_index_with_demo(index_dir: Path) -> None:
    records = [
        ToolRecord(
            id="skill:demo",
            name="demo",
            description="Demo skill for planning",
            source_path="skills/shared/demo/SKILL.md",
            tool_kind="skill",
            metadata={"enabled_targets": []},
        ),
        ToolRecord(
            id="toolchain:codex",
            name="codex",
            description="Codex adapter",
            source_path="src/ai_config/executor/adapters/codex.py",
            tool_kind="toolchain_adapter",
            metadata={"enabled_targets": ["codex"]},
            tags=["target:codex", "capability:cli_execution"],
            invoke={"backend": "cli", "command": "codex", "args": [], "timeout_ms": 1000, "env_keys": []},
        ),
    ]
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")


def _approved_plan() -> OrchestrationPlan:
    tool_ref = ToolReference(
        tool_id="skill:demo",
        tool_kind="skill",
        name="demo",
        source_path="skills/shared/demo/SKILL.md",
        selection_reason="Top candidate",
        invoke_summary="skill_markdown: skills/shared/demo/SKILL.md",
        confidence=0.8,
    )
    return OrchestrationPlan(
        plan_id="plan-test",
        revision=1,
        user_goal="Use the demo skill",
        assumptions=["Demo assumption"],
        specialist_route="general",
        candidate_tools=[tool_ref],
        steps=[
            PlanStep(
                step_id="step-1",
                title="Use demo",
                purpose="Inspect the demo skill",
                inputs=["demo"],
                expected_output="Skill preview",
                tool_ref=tool_ref,
                depends_on=[],
                action="run",
                params={},
                working_directory=".",
            )
        ],
        approval_required=True,
        execution_notes="Demo plan",
        feasibility="full",
        notes="Demo plan",
    )


def test_plan_validator_rejects_missing_tool() -> None:
    plan = _approved_plan()
    validation = validate_orchestration_plan(plan, {})
    assert validation.valid is False
    assert any("unknown tool" in error for error in validation.errors)


def test_plan_validator_rejects_dependency_cycle() -> None:
    plan = _approved_plan()
    plan.steps.append(
        PlanStep(
            step_id="step-2",
            title="Cycle",
            purpose="Create a cycle",
            inputs=["demo"],
            expected_output="cycle",
            tool_ref=plan.steps[0].tool_ref,
            depends_on=["step-1"],
        )
    )
    plan.steps[0].depends_on = ["step-2"]
    validation = validate_orchestration_plan(
        plan,
        {"skill:demo": {"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}},
    )
    assert validation.valid is False
    assert any("DAG" in error for error in validation.errors)


def test_planner_fallback_generates_valid_plan(monkeypatch, tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    _build_index_with_demo(index_dir)
    planner = OrchestrationPlanner(index_dir=index_dir, repo_root=tmp_path)
    monkeypatch.setattr(planner, "_get_llm", lambda: None)

    result = planner.create_plan("demo planning task", top_k=3)

    assert result.validation.valid is True
    assert result.plan.steps
    assert result.plan.candidate_tools
    assert result.plan.steps[0].tool_ref.tool_id == "skill:demo"
    assert "plan_id" in json.dumps(result.plan.model_dump())
