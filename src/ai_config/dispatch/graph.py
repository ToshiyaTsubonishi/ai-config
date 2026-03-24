"""LangGraph wiring for the dispatch runtime."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from ai_config.dispatch.dispatcher import dispatch_step
from ai_config.dispatch.evaluator import evaluate_step, finalize
from ai_config.dispatch.planner import plan_tasks, replan_tasks
from ai_config.dispatch.state import DispatchState


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------
def _route_after_plan(state: dict[str, Any]) -> str:
    """After planning, dispatch first step or finalize (dry-run / error)."""
    if state.get("done"):
        return "finalize"
    return "dispatch_step"


def _route_after_evaluate(state: dict[str, Any]) -> str:
    """After evaluating a step result, decide next action."""
    if state.get("done"):
        return "finalize"
    if state.get("needs_replanning"):
        return "replan_tasks"
    return "dispatch_step"


def _route_after_replan(state: dict[str, Any]) -> str:
    """After replanning, dispatch or abort."""
    if state.get("done") or state.get("abort"):
        return "finalize"
    return "dispatch_step"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
def build_dispatch_graph() -> StateGraph:
    """Build the LangGraph state graph for dispatch execution."""
    graph = StateGraph(DispatchState)

    # Nodes
    graph.add_node("plan_tasks", plan_tasks)
    graph.add_node("dispatch_step", dispatch_step)
    graph.add_node("evaluate_step", evaluate_step)
    graph.add_node("replan_tasks", replan_tasks)
    graph.add_node("finalize", finalize)

    # Edges
    graph.set_entry_point("plan_tasks")

    graph.add_conditional_edges(
        "plan_tasks",
        _route_after_plan,
        {"dispatch_step": "dispatch_step", "finalize": "finalize"},
    )

    graph.add_edge("dispatch_step", "evaluate_step")

    graph.add_conditional_edges(
        "evaluate_step",
        _route_after_evaluate,
        {
            "dispatch_step": "dispatch_step",
            "replan_tasks": "replan_tasks",
            "finalize": "finalize",
        },
    )

    graph.add_conditional_edges(
        "replan_tasks",
        _route_after_replan,
        {"dispatch_step": "dispatch_step", "finalize": "finalize"},
    )

    graph.add_edge("finalize", END)

    return graph


def create_dispatch_agent():
    """Create and compile the dispatch agent graph."""
    return build_dispatch_graph().compile()
