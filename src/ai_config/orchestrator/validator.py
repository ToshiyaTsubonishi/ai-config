"""Validation helpers for orchestration plans."""

from __future__ import annotations

from collections import deque
from typing import Any

from ai_config.orchestrator.plan_schema import OrchestrationPlan, PlanValidationResult
from ai_config.registry.models import ToolRecord


def collect_plan_tool_ids(plan: OrchestrationPlan) -> set[str]:
    """Collect every primary and fallback tool id referenced by a plan."""
    tool_ids = {step.tool_ref.tool_id for step in plan.steps if step.tool_ref.tool_id}
    for step in plan.steps:
        if step.fallback_strategy.fallback_tool_id:
            tool_ids.add(step.fallback_strategy.fallback_tool_id)
    return tool_ids


def validate_orchestration_plan(
    plan: OrchestrationPlan,
    available_tools: dict[str, ToolRecord | dict[str, Any]],
) -> PlanValidationResult:
    """Validate a plan against registry-backed tool records."""
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
            record_tool_kind = record.tool_kind
            record_name = record.name
            record_source_path = record.source_path

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


def _has_cycle(plan: OrchestrationPlan) -> bool:
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

