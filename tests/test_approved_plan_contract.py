from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_config.contracts.approved_plan import (
    APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION,
    APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION,
    APPROVED_PLAN_SCHEMA_VERSION,
    ApprovedPlan,
    ApprovedPlanExecutionRequest,
    ApprovedPlanExecutionResult,
    ApprovedPlanExecutionRuntime,
    ApprovedPlanExecutionStepResult,
    PlanStep,
    ToolReference,
    approved_plan_execution_request_json_schema,
    approved_plan_execution_result_json_schema,
    validate_execution_result_against_request,
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
    result = ApprovedPlanExecutionResult(
        plan_id=plan.plan_id,
        plan_revision=plan.revision,
        execution_id="exec-1",
        runtime=ApprovedPlanExecutionRuntime(name="ai-config-dispatch"),
        status="success",
        final_report="ok",
        step_results=[ApprovedPlanExecutionStepResult(step_id="step-1", status="success")],
    )

    assert plan.kind == "ai-config.approved-plan"
    assert plan.schema_version == APPROVED_PLAN_SCHEMA_VERSION
    assert request.kind == "ai-config.approved-plan-execution-request"
    assert request.schema_version == APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION
    assert result.kind == "ai-config.approved-plan-execution-result"
    assert result.schema_version == APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION

    schema = approved_plan_execution_request_json_schema()
    assert "schema_version" in schema["properties"]
    assert schema["properties"]["schema_version"]["default"] == APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION
    result_schema = approved_plan_execution_result_json_schema()
    assert "schema_version" in result_schema["properties"]
    assert result_schema["properties"]["schema_version"]["default"] == APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION


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


def test_execution_result_rejects_unsupported_major_schema_version() -> None:
    with pytest.raises(ValidationError):
        ApprovedPlanExecutionResult.model_validate(
            {
                "kind": "ai-config.approved-plan-execution-result",
                "schema_version": "2.0.0",
                "plan_id": "plan-1",
                "plan_revision": 1,
                "execution_id": "exec-1",
                "runtime": {"name": "ai-config-dispatch"},
                "status": "success",
                "final_report": "ok",
                "step_results": [{"step_id": "step-1", "status": "success"}],
            }
        )


def test_execution_result_enforces_status_and_error_semantics() -> None:
    with pytest.raises(ValidationError):
        ApprovedPlanExecutionResult(
            plan_id="plan-1",
            plan_revision=1,
            execution_id="exec-1",
            runtime=ApprovedPlanExecutionRuntime(name="ai-config-dispatch"),
            status="success",
            final_report="ok",
            error="should not exist",
            step_results=[ApprovedPlanExecutionStepResult(step_id="step-1", status="success")],
        )

    with pytest.raises(ValidationError):
        ApprovedPlanExecutionResult(
            plan_id="plan-1",
            plan_revision=1,
            execution_id="exec-1",
            runtime=ApprovedPlanExecutionRuntime(name="ai-config-dispatch"),
            status="error",
            final_report="failed",
            step_results=[ApprovedPlanExecutionStepResult(step_id="step-1", status="error", error="boom")],
        )

    with pytest.raises(ValidationError):
        ApprovedPlanExecutionStepResult(step_id="step-1", status="error")

    with pytest.raises(ValidationError):
        ApprovedPlanExecutionStepResult(step_id="step-1", status="success", error="unexpected")

    partial = ApprovedPlanExecutionResult(
        plan_id="plan-1",
        plan_revision=1,
        execution_id="exec-1",
        runtime=ApprovedPlanExecutionRuntime(name="ai-config-dispatch"),
        status="partial",
        final_report="needs replan",
        replan_request={"reason": "execution_failure"},
        step_results=[ApprovedPlanExecutionStepResult(step_id="step-1", status="error", error="boom")],
    )
    assert partial.error is None


def test_execution_result_must_echo_request_identity() -> None:
    plan = _plan()
    request = ApprovedPlanExecutionRequest(
        plan=plan,
        repo_root=".",
        tool_records=[{"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}],
    )

    with pytest.raises(ValueError):
        validate_execution_result_against_request(
            {
                "plan_id": "plan-other",
                "plan_revision": plan.revision,
                "execution_id": "exec-1",
                "runtime": {"name": "ai-config-dispatch"},
                "status": "success",
                "final_report": "ok",
                "step_results": [{"step_id": "step-1", "status": "success"}],
            },
            request,
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
