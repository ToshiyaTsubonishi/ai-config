"""Heuristic specialist router for single-graph orchestration."""

from __future__ import annotations

from typing import Any

SPECIALIST_GENERAL = "general"
SPECIALIST_KNOWLEDGE_WORK = "knowledge_work"
SPECIALIST_SOFTWARE_ENGINEERING = "software_engineering"
SPECIALIST_DATA_ANALYTICS = "data_analytics"

MIN_SPECIALIST_SCORE = 1.0
SPECIALIST_CANDIDATE_THRESHOLD = 3

_SPECIALIST_KEYWORDS: dict[str, tuple[str, ...]] = {
    SPECIALIST_KNOWLEDGE_WORK: (
        "sales",
        "support",
        "marketing",
        "finance",
        "legal",
        "hr",
        "customer",
        "call prep",
        "outreach",
        "pipeline",
        "stakeholder",
        "enterprise search",
        "cowork",
        "plugin",
    ),
    SPECIALIST_SOFTWARE_ENGINEERING: (
        "code",
        "bug",
        "fix",
        "test",
        "build",
        "react",
        "typescript",
        "python",
        "api",
        "refactor",
        "deploy",
        "ci",
        "hook",
        "lint",
    ),
    SPECIALIST_DATA_ANALYTICS: (
        "sql",
        "data",
        "analytics",
        "analysis",
        "dashboard",
        "metric",
        "kpi",
        "query",
        "dataset",
        "snowflake",
        "databricks",
        "bigquery",
        "warehouse",
    ),
}

_SPECIALIST_FILTERS: dict[str, dict[str, Any]] = {
    SPECIALIST_KNOWLEDGE_WORK: {
        "source_repos": ["anthropics-knowledge-work-plugins", "anthropics-skills"],
        "tool_kinds": ["skill", "mcp_server"],
    },
    SPECIALIST_SOFTWARE_ENGINEERING: {
        "domains": ["shared", "custom", "engineering", "development", "devops", "testing", "toolchain"],
        "tool_kinds": ["skill", "skill_script", "mcp_server", "toolchain_adapter"],
    },
    SPECIALIST_DATA_ANALYTICS: {
        "domains": ["data", "analytics", "finance", "enterprise-search"],
        "tool_kinds": ["skill", "mcp_server", "skill_script"],
    },
    SPECIALIST_GENERAL: {},
}


def route_specialist(query: str) -> tuple[str, float]:
    q = query.lower().strip()
    if not q:
        return SPECIALIST_GENERAL, 0.0

    scores: dict[str, float] = {}
    for specialist, keywords in _SPECIALIST_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in q:
                score += 1.0 if " " not in keyword else 1.5
        scores[specialist] = score

    best_specialist = max(scores, key=lambda k: scores[k])
    best_score = float(scores[best_specialist])
    if best_score < MIN_SPECIALIST_SCORE:
        return SPECIALIST_GENERAL, 0.0
    return best_specialist, best_score


def specialist_filters(specialist: str) -> dict[str, Any]:
    return dict(_SPECIALIST_FILTERS.get(specialist, {}))
