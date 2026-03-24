"""Compatibility wrapper for approved plan contracts.

New code should import from ``ai_config.contracts.approved_plan``.
"""

from ai_config.contracts.approved_plan import (
    APPROVED_PLAN_KIND,
    APPROVED_PLAN_SCHEMA_VERSION,
    ApprovedPlan as OrchestrationPlan,
    FallbackStrategy,
    PlanObject,
    PlanStep,
    PlanValidationResult,
    ToolReference,
    parse_plan_text,
    plan_from_dict,
)

__all__ = [
    "APPROVED_PLAN_KIND",
    "APPROVED_PLAN_SCHEMA_VERSION",
    "OrchestrationPlan",
    "ToolReference",
    "FallbackStrategy",
    "PlanStep",
    "PlanValidationResult",
    "PlanObject",
    "plan_from_dict",
    "parse_plan_text",
]
