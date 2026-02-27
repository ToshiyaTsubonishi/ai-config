"""State definition for the LangGraph orchestrator."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State passed between nodes in the orchestration graph.

    Fields:
        query: The original user request.
        retrieved_tools: Tool records found by the retriever.
        plan: LLM-generated execution plan as structured text.
        execution_results: Accumulated results from tool executions.
        error: Error message if any step failed.
        retry_count: Number of retrieve-retry cycles performed.
        final_answer: The response to return to the user.
    """

    query: str
    retrieved_tools: list[dict[str, Any]]
    plan: str
    execution_results: list[dict[str, Any]]
    error: str | None
    retry_count: int
    final_answer: str
