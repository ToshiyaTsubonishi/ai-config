"""LangGraph wiring for dynamic retrieve-plan-execute-repair loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from ai_config.orchestrator import nodes
from ai_config.orchestrator.state import AgentState


def _route_after_plan(state: dict[str, Any]) -> str:
    return "finalize" if state.get("done") else "execute_step"


def _route_after_evaluate(state: dict[str, Any]) -> str:
    if state.get("done"):
        return "finalize"
    if state.get("needs_repair"):
        return "repair_or_fallback"
    return "execute_step"


def _route_after_repair(state: dict[str, Any]) -> str:
    if state.get("abort") or state.get("done"):
        return "finalize"
    if state.get("require_reretrieve"):
        return "re_retrieve"
    return "execute_step"


def _route_after_reretrieve(state: dict[str, Any]) -> str:
    if state.get("reretrieve_failed"):
        return "finalize"
    return "plan_steps"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_candidates", nodes.retrieve_candidates)
    graph.add_node("plan_steps", nodes.plan_steps)
    graph.add_node("execute_step", nodes.execute_step)
    graph.add_node("evaluate_step", nodes.evaluate_step)
    graph.add_node("repair_or_fallback", nodes.repair_or_fallback)
    graph.add_node("re_retrieve", nodes.re_retrieve)
    graph.add_node("finalize", nodes.finalize)

    graph.set_entry_point("retrieve_candidates")
    graph.add_edge("retrieve_candidates", "plan_steps")
    graph.add_conditional_edges("plan_steps", _route_after_plan, {"execute_step": "execute_step", "finalize": "finalize"})
    graph.add_edge("execute_step", "evaluate_step")
    graph.add_conditional_edges(
        "evaluate_step",
        _route_after_evaluate,
        {
            "execute_step": "execute_step",
            "repair_or_fallback": "repair_or_fallback",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "repair_or_fallback",
        _route_after_repair,
        {
            "execute_step": "execute_step",
            "re_retrieve": "re_retrieve",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges("re_retrieve", _route_after_reretrieve, {"plan_steps": "plan_steps", "finalize": "finalize"})
    graph.add_edge("finalize", END)

    return graph


def create_agent(index_dir: Path | None = None, repo_root: Path | None = None):
    nodes.configure_runtime(index_dir=index_dir, repo_root=repo_root)
    return build_graph().compile()
