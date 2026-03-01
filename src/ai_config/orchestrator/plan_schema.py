"""Structured plan schema for orchestrator."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class PlanStep(BaseModel):
    step_id: str = Field(..., description="Stable step identifier")
    tool_id: str = Field(..., description="Tool record id")
    action: str = Field(default="run", description="Action name")
    reason: str = Field(default="", description="Why this step exists")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool call parameters")


class PlanObject(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    feasibility: Literal["full", "partial", "impossible"] = "partial"
    notes: str = ""


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
        # Last-resort: impossible plan with captured diagnostics.
        return PlanObject(steps=[], feasibility="impossible", notes=f"Invalid planner output: {text[:300]}")

    try:
        return PlanObject.model_validate(parsed)
    except ValidationError as exc:
        return PlanObject(steps=[], feasibility="impossible", notes=f"Plan schema validation failed: {exc}")
