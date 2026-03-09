"""Structured plan schema for planning-first orchestration."""

from __future__ import annotations

import json
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError, model_validator


def _new_plan_id() -> str:
    return f"plan-{uuid4().hex[:10]}"


class ToolReference(BaseModel):
    """Resolved tool metadata attached to an orchestration plan."""

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
    """A single executable plan step."""

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
        """Legacy accessor used by the existing orchestrator graph."""
        return self.tool_ref.tool_id

    @tool_id.setter
    def tool_id(self, value: str) -> None:
        self.tool_ref.tool_id = value


class OrchestrationPlan(BaseModel):
    """Durable orchestration artifact returned before execution."""

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


class PlanValidationResult(BaseModel):
    """Validation output for a plan artifact."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# Backward-compatible alias used by the legacy graph implementation.
PlanObject = OrchestrationPlan


def plan_from_dict(raw: dict[str, Any]) -> OrchestrationPlan:
    return OrchestrationPlan.model_validate(raw)


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
