"""LangGraph state graph definition for the orchestrator.

Implements the core agent loop:
  retrieve → plan → execute → evaluate → (respond | retry retrieve)
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from ai_config.orchestrator.state import AgentState
from ai_config.orchestrator.nodes import (
    retrieve,
    plan,
    execute,
    evaluate,
    respond,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def _should_retry(state: dict[str, Any]) -> str:
    """Conditional edge: decide whether to retry or respond."""
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    if error and retry_count < MAX_RETRIES:
        logger.info("Routing to retry (count=%d)", retry_count)
        return "retry"
    return "done"


def build_graph() -> StateGraph:
    """Construct and compile the orchestration graph.

    Graph topology:
        ┌──────────┐
        │ retrieve  │◀──────┐
        └────┬─────┘       │
             ▼              │
        ┌──────────┐       │
        │   plan   │       │
        └────┬─────┘       │
             ▼              │
        ┌──────────┐       │
        │ execute  │       │
        └────┬─────┘       │
             ▼              │
        ┌──────────┐       │
        │ evaluate │───────┘  (retry)
        └────┬─────┘
             │ (done)
             ▼
        ┌──────────┐
        │ respond  │
        └────┬─────┘
             ▼
            END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", retrieve)
    graph.add_node("plan", plan)
    graph.add_node("execute", execute)
    graph.add_node("evaluate", evaluate)
    graph.add_node("respond", respond)

    # Linear edges
    graph.add_edge("retrieve", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "evaluate")

    # Conditional edge from evaluate
    graph.add_conditional_edges(
        "evaluate",
        _should_retry,
        {
            "retry": "retrieve",
            "done": "respond",
        },
    )

    graph.add_edge("respond", END)

    # Entry point
    graph.set_entry_point("retrieve")

    return graph


def create_agent():
    """Create a compiled agent ready to invoke."""
    graph = build_graph()
    return graph.compile()
