"""State definition for LangGraph orchestration."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    top_k: int
    max_retries: int
    trace: bool
    specialist: str
    specialist_score: float
    specialist_fallback_used: bool

    retrieval_attempts: int
    candidates: list[dict[str, Any]]
    intent: dict[str, Any]

    plan: dict[str, Any]
    current_step: int
    step_retry_count: int
    require_reretrieve: bool
    reretrieve_failed: bool
    done: bool
    abort: bool
    needs_repair: bool

    execution_results: list[dict[str, Any]]
    last_step_result: dict[str, Any] | None
    recovery_path: list[str]
    adopted_tools: list[str]
    unmet: list[str]
    error: str | None
    final_answer: str
