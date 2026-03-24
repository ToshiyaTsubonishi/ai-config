"""Stable plan and execution contracts shared across ai-config boundaries."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError, model_validator

APPROVED_PLAN_KIND = "ai-config.approved-plan"
APPROVED_PLAN_SCHEMA_VERSION = "1.0.0"
APPROVED_PLAN_EXECUTION_REQUEST_KIND = "ai-config.approved-plan-execution-request"
APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION = "1.0.0"
APPROVED_PLAN_EXECUTION_RESULT_KIND = "ai-config.approved-plan-execution-result"
APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION = "1.0.0"
_SUPPORTED_SCHEMA_MAJOR = 1


def _new_plan_id() -> str:
    return f"plan-{uuid4().hex[:10]}"


def _schema_major(version: str) -> int:
    try:
        return int(str(version).split(".", 1)[0])
    except (TypeError, ValueError):
        raise ValueError(f"Invalid schema_version: {version}") from None


def _ensure_supported_schema(kind: str, schema_version: str, expected_kind: str) -> None:
    if kind != expected_kind:
        raise ValueError(f"Unexpected contract kind: {kind}")
    if _schema_major(schema_version) != _SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(
            f"Unsupported schema_version={schema_version} for {expected_kind}. "
            f"Supported major version is {_SUPPORTED_SCHEMA_MAJOR}.x.x."
        )


class ToolReference(BaseModel):
    """Resolved tool metadata attached to an approved plan."""

    tool_id: str = Field(..., description="Stable tool record identifier")
    tool_kind: str = Field(default="", description="Tool kind from ToolRecord")
    name: str = Field(default="", description="Human-readable tool name")
    source_path: str = Field(default="", description="Relative source path")
    selection_reason: str = Field(default="", description="Why this tool was selected")
    invoke_summary: str = Field(default="", description="Compact invocation summary")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FallbackStrategy(BaseModel):
    """Plan-time fallback policy for a step."""

    action: Literal["retry", "use_alternative_tool", "replan", "abort"] = "replan"
    fallback_tool_id: str | None = None
    notes: str = ""


class PlanStep(BaseModel):
    """A single executable step within an approved plan."""

    step_id: str = Field(..., description="Stable step identifier")
    title: str = Field(default="", description="Short step title")
    purpose: str = Field(default="", description="Why this step exists")
    reason: str = Field(default="", description="Legacy compatibility alias for purpose")
    inputs: list[str] = Field(default_factory=list, description="Named or human-readable inputs")
    expected_output: str = Field(default="", description="Expected step output")
    tool_ref: ToolReference
    depends_on: list[str] = Field(default_factory=list)
    fallback_strategy: FallbackStrategy = Field(default_factory=FallbackStrategy)
    action: str = Field(default="run", description="Execution action")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool call parameters")
    working_directory: str = Field(default=".", description="Execution directory")

    @model_validator(mode="before")
    @classmethod
    def _compat_from_legacy(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        if "purpose" not in payload and payload.get("reason"):
            payload["purpose"] = payload["reason"]
        if "reason" not in payload and payload.get("purpose"):
            payload["reason"] = payload["purpose"]
        if "title" not in payload:
            payload["title"] = payload.get("purpose") or payload.get("reason") or payload.get("step_id", "")
        if "expected_output" not in payload:
            payload["expected_output"] = ""
        if "inputs" not in payload or payload["inputs"] is None:
            payload["inputs"] = []

        tool_ref = payload.get("tool_ref")
        if tool_ref is None and payload.get("tool_id"):
            payload["tool_ref"] = {
                "tool_id": payload.get("tool_id", ""),
                "tool_kind": payload.get("tool_kind", ""),
                "name": payload.get("tool_name", ""),
                "source_path": payload.get("source_path", ""),
                "selection_reason": payload.get("purpose") or payload.get("reason", ""),
                "invoke_summary": payload.get("invoke_summary", ""),
                "confidence": float(payload.get("confidence", 0.0) or 0.0),
            }

        fallback = payload.get("fallback_strategy")
        if fallback is None:
            payload["fallback_strategy"] = {
                "action": "replan",
                "fallback_tool_id": payload.get("fallback_tool_id"),
                "notes": "",
            }
        elif isinstance(fallback, str):
            payload["fallback_strategy"] = {"action": "replan", "fallback_tool_id": None, "notes": fallback}

        return payload

    @model_validator(mode="after")
    def _sync_reason_fields(self) -> PlanStep:
        if not self.purpose and self.reason:
            self.purpose = self.reason
        if not self.reason and self.purpose:
            self.reason = self.purpose
        if not self.title:
            self.title = self.purpose or self.reason or self.step_id
        return self

    @property
    def tool_id(self) -> str:
        return self.tool_ref.tool_id

    @tool_id.setter
    def tool_id(self, value: str) -> None:
        self.tool_ref.tool_id = value


class ApprovedPlan(BaseModel):
    """Stable artifact approved by planner and consumable by execution runtimes."""

    kind: str = Field(default=APPROVED_PLAN_KIND)
    schema_version: str = Field(default=APPROVED_PLAN_SCHEMA_VERSION)
    plan_id: str = Field(default_factory=_new_plan_id)
    revision: int = Field(default=1, ge=1)
    user_goal: str = Field(default="")
    assumptions: list[str] = Field(default_factory=list)
    specialist_route: str = Field(default="general")
    candidate_tools: list[ToolReference] = Field(default_factory=list)
    steps: list[PlanStep] = Field(default_factory=list)
    approval_required: bool = True
    execution_notes: str = ""
    feasibility: Literal["full", "partial", "impossible"] = "partial"
    notes: str = ""
    replan_reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def _compat_from_legacy(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        payload.setdefault("kind", APPROVED_PLAN_KIND)
        payload.setdefault("schema_version", APPROVED_PLAN_SCHEMA_VERSION)
        payload.setdefault("plan_id", _new_plan_id())
        payload.setdefault("revision", 1)
        payload.setdefault("user_goal", payload.get("query", ""))
        payload.setdefault("assumptions", [])
        payload.setdefault("specialist_route", payload.get("specialist", "general"))
        payload.setdefault("candidate_tools", [])
        payload.setdefault("approval_required", True)
        payload.setdefault("execution_notes", payload.get("notes", ""))
        payload.setdefault("notes", payload.get("execution_notes", ""))
        payload.setdefault("replan_reason", "")
        return payload

    @model_validator(mode="after")
    def _validate_contract(self) -> ApprovedPlan:
        _ensure_supported_schema(self.kind, self.schema_version, APPROVED_PLAN_KIND)
        return self


class ApprovedPlanExecutionRequest(BaseModel):
    """Stable execution request passed from ai-config planner to an execution runtime."""

    kind: str = Field(default=APPROVED_PLAN_EXECUTION_REQUEST_KIND)
    schema_version: str = Field(default=APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION)
    plan: ApprovedPlan
    repo_root: str
    working_directory: str = "."
    tool_records: list[dict[str, Any]] = Field(default_factory=list)
    max_retries: int = Field(default=0, ge=0)
    parallel: bool = False
    keep_context: bool = False

    @model_validator(mode="before")
    @classmethod
    def _compat_from_legacy(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        payload.setdefault("kind", APPROVED_PLAN_EXECUTION_REQUEST_KIND)
        payload.setdefault("schema_version", APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION)
        if "plan" not in payload and payload.get("approved_plan") is not None:
            payload["plan"] = payload["approved_plan"]
        if "working_directory" not in payload and payload.get("repo_root"):
            payload["working_directory"] = payload["repo_root"]
        return payload

    @model_validator(mode="after")
    def _validate_contract(self) -> ApprovedPlanExecutionRequest:
        _ensure_supported_schema(
            self.kind,
            self.schema_version,
            APPROVED_PLAN_EXECUTION_REQUEST_KIND,
        )
        if not self.repo_root:
            raise ValueError("repo_root must not be empty.")
        tool_record_ids = [str(record.get("id", "")) for record in self.tool_records if isinstance(record, dict)]
        missing_tool_ids = [
            tool_id for tool_id in collect_plan_tool_ids(self.plan) if tool_record_ids and tool_id not in tool_record_ids
        ]
        if missing_tool_ids:
            raise ValueError(
                "tool_records must cover every referenced tool_id when provided: "
                + ", ".join(sorted(set(missing_tool_ids)))
            )
        return self


class ApprovedPlanExecutionRuntime(BaseModel):
    """Execution runtime metadata echoed back by a stable result contract."""

    name: str = Field(..., description="Stable runtime identifier")
    version: str = Field(default="", description="Runtime package or build version")
    transport: str = Field(default="subprocess_json", description="Boundary transport")

    @model_validator(mode="after")
    def _validate_runtime(self) -> ApprovedPlanExecutionRuntime:
        if not self.name:
            raise ValueError("runtime.name must not be empty.")
        if not self.transport:
            raise ValueError("runtime.transport must not be empty.")
        return self


class ApprovedPlanExecutionStepResult(BaseModel):
    """Stable per-step execution outcome."""

    step_id: str = Field(..., description="Stable step identifier from the approved plan")
    status: Literal["success", "skipped", "error", "aborted", "timeout"] = "success"
    agent: str = Field(default="", description="Execution agent or worker identifier")
    tool_id: str = Field(default="", description="Resolved tool identifier")
    action: str = Field(default="", description="Execution action")
    retry_count: int = Field(default=0, ge=0, description="Number of retries consumed")
    output_summary: str = Field(default="", description="Compact output summary")
    error: str | None = Field(default=None, description="Step-level error message")

    @model_validator(mode="before")
    @classmethod
    def _compat_from_runtime(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        payload.setdefault("status", "error" if payload.get("error") else "success")
        if "retry_count" not in payload:
            payload["retry_count"] = payload.get("retry_attempt", payload.get("retries", 0))
        if "output_summary" not in payload or payload.get("output_summary") is None:
            output = payload.get("output")
            if output is None:
                payload["output_summary"] = ""
            elif isinstance(output, str):
                payload["output_summary"] = output
            else:
                payload["output_summary"] = json.dumps(output, ensure_ascii=False, default=str)
        return payload

    @model_validator(mode="after")
    def _validate_step_status(self) -> ApprovedPlanExecutionStepResult:
        if not self.step_id:
            raise ValueError("step_id must not be empty.")
        if self.error is not None and not self.error.strip():
            self.error = None
        if self.status in {"error", "aborted", "timeout"} and self.error is None:
            raise ValueError(f"step {self.step_id} requires error when status={self.status}.")
        if self.status in {"success", "skipped"} and self.error is not None:
            raise ValueError(f"step {self.step_id} must not include error when status={self.status}.")
        return self


class ApprovedPlanExecutionResult(BaseModel):
    """Stable execution result returned by a runtime boundary."""

    kind: str = Field(default=APPROVED_PLAN_EXECUTION_RESULT_KIND)
    schema_version: str = Field(default=APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION)
    request_kind: str = Field(default=APPROVED_PLAN_EXECUTION_REQUEST_KIND)
    request_schema_version: str = Field(default=APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION)
    plan_id: str
    plan_revision: int = Field(..., ge=1)
    execution_id: str
    runtime: ApprovedPlanExecutionRuntime
    status: Literal["success", "partial", "error", "aborted"] = "success"
    final_report: str = ""
    step_results: list[ApprovedPlanExecutionStepResult] = Field(default_factory=list)
    replan_request: dict[str, Any] | None = None
    error: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _compat_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        payload.setdefault("kind", APPROVED_PLAN_EXECUTION_RESULT_KIND)
        payload.setdefault("schema_version", APPROVED_PLAN_EXECUTION_RESULT_SCHEMA_VERSION)
        payload.setdefault("request_kind", APPROVED_PLAN_EXECUTION_REQUEST_KIND)
        payload.setdefault("request_schema_version", APPROVED_PLAN_EXECUTION_REQUEST_SCHEMA_VERSION)
        payload.setdefault("step_results", [])
        payload.setdefault("final_report", "")
        if "plan_revision" not in payload and payload.get("revision") is not None:
            payload["plan_revision"] = payload.get("revision")
        return payload

    @model_validator(mode="after")
    def _validate_contract(self) -> ApprovedPlanExecutionResult:
        _ensure_supported_schema(
            self.kind,
            self.schema_version,
            APPROVED_PLAN_EXECUTION_RESULT_KIND,
        )
        _ensure_supported_schema(
            self.request_kind,
            self.request_schema_version,
            APPROVED_PLAN_EXECUTION_REQUEST_KIND,
        )
        if not self.plan_id:
            raise ValueError("plan_id must not be empty.")
        if not self.execution_id:
            raise ValueError("execution_id must not be empty.")

        step_ids = [step.step_id for step in self.step_results]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step result IDs are not allowed.")

        terminal_step_failures = [
            step.step_id for step in self.step_results if step.status in {"error", "aborted", "timeout"}
        ]
        if self.error is not None and not self.error.strip():
            self.error = None

        if self.status == "success":
            if self.error is not None:
                raise ValueError("status=success must not include top-level error.")
            if self.replan_request is not None:
                raise ValueError("status=success must not include replan_request.")
            if terminal_step_failures:
                raise ValueError("status=success must not include failed step results.")
        elif self.status == "partial":
            if self.error is not None:
                raise ValueError("status=partial must not include top-level error.")
            if self.replan_request is None:
                raise ValueError("status=partial requires replan_request.")
        elif self.status in {"error", "aborted"}:
            if self.error is None:
                raise ValueError(f"status={self.status} requires top-level error.")
            if self.replan_request is not None:
                raise ValueError(f"status={self.status} must not include replan_request.")

        return self


class PlanValidationResult(BaseModel):
    """Validation output for an approved plan artifact."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


OrchestrationPlan = ApprovedPlan
PlanObject = ApprovedPlan


def plan_from_dict(raw: dict[str, Any]) -> ApprovedPlan:
    return ApprovedPlan.model_validate(raw)


def parse_plan_text(raw_text: str) -> PlanObject:
    text = raw_text.strip()
    candidate = text
    if "```json" in text:
        candidate = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        candidate = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return PlanObject(
            steps=[],
            feasibility="impossible",
            notes=f"Invalid planner output: {text[:300]}",
            execution_notes=f"Invalid planner output: {text[:300]}",
        )

    try:
        return PlanObject.model_validate(parsed)
    except ValidationError as exc:
        message = f"Plan schema validation failed: {exc}"
        return PlanObject(steps=[], feasibility="impossible", notes=message, execution_notes=message)


def load_approved_plan_execution_request(raw_or_path: str | Path) -> ApprovedPlanExecutionRequest:
    path = Path(str(raw_or_path))
    raw_text = path.read_text(encoding="utf-8") if path.exists() else str(raw_or_path)
    return ApprovedPlanExecutionRequest.model_validate_json(raw_text)


def load_approved_plan_execution_result(raw_or_path: str | Path) -> ApprovedPlanExecutionResult:
    path = Path(str(raw_or_path))
    raw_text = path.read_text(encoding="utf-8") if path.exists() else str(raw_or_path)
    return ApprovedPlanExecutionResult.model_validate_json(raw_text)


def approved_plan_json_schema() -> dict[str, Any]:
    return ApprovedPlan.model_json_schema()


def approved_plan_execution_request_json_schema() -> dict[str, Any]:
    return ApprovedPlanExecutionRequest.model_json_schema()


def approved_plan_execution_result_json_schema() -> dict[str, Any]:
    return ApprovedPlanExecutionResult.model_json_schema()


def validate_execution_result_against_request(
    result: ApprovedPlanExecutionResult | dict[str, Any],
    request: ApprovedPlanExecutionRequest | dict[str, Any],
) -> ApprovedPlanExecutionResult:
    parsed_result = (
        result if isinstance(result, ApprovedPlanExecutionResult) else ApprovedPlanExecutionResult.model_validate(result)
    )
    parsed_request = (
        request if isinstance(request, ApprovedPlanExecutionRequest) else ApprovedPlanExecutionRequest.model_validate(request)
    )

    errors: list[str] = []
    if parsed_result.request_kind != parsed_request.kind:
        errors.append(f"request_kind mismatch: {parsed_result.request_kind} != {parsed_request.kind}")
    if parsed_result.request_schema_version != parsed_request.schema_version:
        errors.append(
            "request_schema_version mismatch: "
            f"{parsed_result.request_schema_version} != {parsed_request.schema_version}"
        )
    if parsed_result.plan_id != parsed_request.plan.plan_id:
        errors.append(f"plan_id mismatch: {parsed_result.plan_id} != {parsed_request.plan.plan_id}")
    if parsed_result.plan_revision != parsed_request.plan.revision:
        errors.append(f"plan_revision mismatch: {parsed_result.plan_revision} != {parsed_request.plan.revision}")
    if errors:
        raise ValueError("Execution result/request mismatch: " + "; ".join(errors))
    return parsed_result


def collect_plan_tool_ids(plan: ApprovedPlan) -> set[str]:
    tool_ids = {step.tool_ref.tool_id for step in plan.steps if step.tool_ref.tool_id}
    for step in plan.steps:
        if step.fallback_strategy.fallback_tool_id:
            tool_ids.add(step.fallback_strategy.fallback_tool_id)
    return tool_ids


def validate_approved_plan(
    plan: ApprovedPlan,
    available_tools: dict[str, Any],
) -> PlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not plan.user_goal:
        warnings.append("Plan user_goal is empty.")
    if not plan.steps:
        warnings.append("Plan has no steps.")

    step_ids = [step.step_id for step in plan.steps]
    unique_step_ids = set(step_ids)
    if len(step_ids) != len(unique_step_ids):
        errors.append("Duplicate step IDs are not allowed.")

    for step in plan.steps:
        if not step.step_id:
            errors.append("Every step must include step_id.")
        if not step.tool_ref.tool_id:
            errors.append(f"Step {step.step_id or '?'} is missing tool_ref.tool_id.")
            continue

        record = available_tools.get(step.tool_ref.tool_id)
        if record is None:
            errors.append(f"Step {step.step_id} references unknown tool: {step.tool_ref.tool_id}")
            continue

        if isinstance(record, dict):
            record_tool_kind = str(record.get("tool_kind", ""))
            record_name = str(record.get("name", ""))
            record_source_path = str(record.get("source_path", ""))
        else:
            record_tool_kind = str(getattr(record, "tool_kind", ""))
            record_name = str(getattr(record, "name", ""))
            record_source_path = str(getattr(record, "source_path", ""))

        if step.tool_ref.tool_kind and step.tool_ref.tool_kind != record_tool_kind:
            errors.append(
                f"Step {step.step_id} has ambiguous tool kind for {step.tool_ref.tool_id}: "
                f"{step.tool_ref.tool_kind} != {record_tool_kind}"
            )
        if step.tool_ref.name and step.tool_ref.name != record_name:
            warnings.append(
                f"Step {step.step_id} tool name differs from registry for {step.tool_ref.tool_id}: "
                f"{step.tool_ref.name} != {record_name}"
            )
        if step.tool_ref.source_path and step.tool_ref.source_path != record_source_path:
            warnings.append(
                f"Step {step.step_id} source_path differs from registry for {step.tool_ref.tool_id}: "
                f"{step.tool_ref.source_path} != {record_source_path}"
            )

        for dep in step.depends_on:
            if dep not in unique_step_ids:
                errors.append(f"Step {step.step_id} depends on unknown step: {dep}")

        fallback_tool_id = step.fallback_strategy.fallback_tool_id
        if fallback_tool_id and fallback_tool_id not in available_tools:
            errors.append(f"Step {step.step_id} fallback tool does not exist: {fallback_tool_id}")

    if not errors and _has_cycle(plan):
        errors.append("Plan step dependencies must form a DAG.")

    return PlanValidationResult(valid=not errors, errors=errors, warnings=warnings)


def render_approved_plan_summary(plan: ApprovedPlan) -> str:
    lines = [
        f"Plan ID: {plan.plan_id} (rev {plan.revision})",
        f"Goal: {plan.user_goal}",
        f"Specialist: {plan.specialist_route}",
        f"Feasibility: {plan.feasibility}",
        f"Approval required: {'yes' if plan.approval_required else 'no'}",
        f"Contract: {plan.kind}@{plan.schema_version}",
        "",
    ]
    if plan.assumptions:
        lines.append("Assumptions:")
        lines.extend(f"- {assumption}" for assumption in plan.assumptions)
        lines.append("")
    if plan.steps:
        lines.append("Steps:")
        for step in plan.steps:
            lines.append(
                f"- {step.step_id}: {step.title} -> {step.tool_ref.tool_id} "
                f"(depends_on={','.join(step.depends_on) or 'none'})"
            )
            lines.append(f"  expected: {step.expected_output or '(not specified)'}")
    else:
        lines.append("Steps: none")
    return "\n".join(lines)


def _has_cycle(plan: ApprovedPlan) -> bool:
    in_degree = {step.step_id: 0 for step in plan.steps}
    edges: dict[str, list[str]] = {step.step_id: [] for step in plan.steps}
    for step in plan.steps:
        for dep in step.depends_on:
            if dep not in in_degree:
                continue
            in_degree[step.step_id] += 1
            edges[dep].append(step.step_id)

    queue = deque(step_id for step_id, degree in in_degree.items() if degree == 0)
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for child in edges.get(current, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    return visited != len(plan.steps)
