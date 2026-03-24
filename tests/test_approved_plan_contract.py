from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_config.contracts.approved_plan import (
    APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION,
    APPROVED_PLAN_SCHEMA_VERSION,
    ApprovedPlan,
    ApprovedPlanExecutionRequest,
    PlanStep,
    ToolReference,
    approved_plan_execution_request_json_schema,
    validate_approved_plan,
)


def _tool_ref(tool_id: str = "skill:demo") -> ToolReference:
    return ToolReference(
        tool_id=tool_id,
        tool_kind="skill",
        name="demo",
        source_path="skills/shared/demo/SKILL.md",
        selection_reason="selected for test",
        invoke_summary="skill_markdown: skills/shared/demo/SKILL.md",
        confidence=0.7,
    )


def _plan(*, depends_on: list[str] | None = None, tool_id: str = "skill:demo") -> ApprovedPlan:
    tool_ref = _tool_ref(tool_id=tool_id)
    return ApprovedPlan(
        user_goal="Inspect the demo skill",
        candidate_tools=[tool_ref],
        steps=[
            PlanStep(
                step_id="step-1",
                title="Open demo",
                purpose="Read the demo skill",
                inputs=["demo"],
                expected_output="content preview",
                tool_ref=tool_ref,
                depends_on=depends_on or [],
            )
        ],
    )


def test_contract_models_default_schema_metadata() -> None:
    plan = _plan()
    request = ApprovedPlanExecutionRequest(
        plan=plan,
        repo_root=".",
        tool_records=[{"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}],
    )

    assert plan.kind == "ai-config.approved-plan"
    assert plan.schema_version == APPROVED_PLAN_SCHEMA_VERSION
    assert request.kind == "ai-config.approved-plan-execution-request"
    assert request.schema_version == APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION

    schema = approved_plan_execution_request_json_schema()
    assert "schema_version" in schema["properties"]
    assert schema["properties"]["schema_version"]["default"] == APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION


def test_execution_request_rejects_unsupported_major_schema_version() -> None:
    with pytest.raises(ValidationError):
        ApprovedPlanExecutionRequest.model_validate(
            {
                "kind": "ai-config.approved-plan-execution-request",
                "schema_version": "2.0.0",
                "repo_root": ".",
                "tool_records": [{"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}],
                "plan": _plan().model_dump(),
            }
        )


def test_validate_approved_plan_reports_unknown_tools_and_cycles() -> None:
    unknown_tool_plan = _plan(tool_id="skill:missing")
    unknown_tool_result = validate_approved_plan(
        unknown_tool_plan,
        {"skill:demo": {"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}},
    )
    assert unknown_tool_result.valid is False
    assert any("unknown tool" in error for error in unknown_tool_result.errors)

    cyclic_plan = ApprovedPlan(
        user_goal="Create a cycle",
        candidate_tools=[_tool_ref()],
        steps=[
            PlanStep(
                step_id="step-1",
                title="First",
                purpose="Cycle start",
                inputs=["demo"],
                expected_output="one",
                tool_ref=_tool_ref(),
                depends_on=["step-2"],
            ),
            PlanStep(
                step_id="step-2",
                title="Second",
                purpose="Cycle end",
                inputs=["demo"],
                expected_output="two",
                tool_ref=_tool_ref(),
                depends_on=["step-1"],
            ),
        ],
    )
    cyclic_result = validate_approved_plan(
        cyclic_plan,
        {"skill:demo": {"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}},
    )
    assert cyclic_result.valid is False
    assert any("DAG" in error for error in cyclic_result.errors)
