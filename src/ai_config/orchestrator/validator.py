"""Compatibility helpers for approved plan validation.

New code should import validation helpers from ``ai_config.contracts``.
"""

from ai_config.contracts.approved_plan import (
    ApprovedPlan as OrchestrationPlan,
    PlanValidationResult,
    collect_plan_tool_ids,
    validate_approved_plan,
)


def validate_orchestration_plan(
    plan: OrchestrationPlan,
    available_tools: dict[str, object],
) -> PlanValidationResult:
    return validate_approved_plan(plan, available_tools)


__all__ = [
    "OrchestrationPlan",
    "PlanValidationResult",
    "collect_plan_tool_ids",
    "validate_orchestration_plan",
]
