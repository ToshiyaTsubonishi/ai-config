"""CLI entrypoint for planning-first orchestrator."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from ai_config.dispatch.graph import create_dispatch_agent
from ai_config.orchestrator.planner import OrchestrationPlanner, render_plan_summary
from ai_config.orchestrator.validator import validate_orchestration_plan
from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.retriever.query_intent import infer_query_intent
from ai_config.runtime_env import load_runtime_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _print_search_only(index_dir: Path, query: str, top_k: int) -> None:
    retriever = HybridRetriever(index_dir)
    intent = infer_query_intent(query)
    hits = retriever.search(
        query=query,
        top_k=top_k,
        tool_kinds=intent.tool_kinds or None,
        targets=intent.targets or None,
        capabilities=intent.capabilities or None,
    )
    if not hits:
        print("No tools found.")
        return
    for idx, hit in enumerate(hits, start=1):
        payload = hit.to_dict()
        score = payload["score_breakdown"]
        print(
            f"{idx}. [{payload['tool_kind']}] {payload['name']} "
            f"(rrf={score['rrf']:.4f}, sem={score['semantic']:.4f}, bm25={score['bm25']:.4f})"
        )
        print(f"   id={payload['id']} source={payload['source_path']}")
        print(f"   {payload['description'][:140]}")


def _execute_approved_plan(
    planner: OrchestrationPlanner,
    plan: Any,
    *,
    repo_root: Path,
    max_retries: int,
    parallel: bool,
    keep_context: bool,
) -> dict[str, Any]:
    agent = create_dispatch_agent()
    resolved_records = [record.to_dict() for record in planner.resolve_records_for_plan(plan).values()]
    initial_state = {
        "user_prompt": plan.user_goal,
        "working_directory": str(repo_root),
        "repo_root": str(repo_root),
        "approved_plan": plan.model_dump(),
        "tool_records": resolved_records,
        "max_retries": max(0, max_retries),
        "max_replans": 0,
        "dry_run": False,
        "parallel": parallel,
        "keep_context": keep_context,
        "step_results": [],
        "replan_count": 0,
        "replan_request": None,
        "done": False,
        "abort": False,
        "needs_replanning": False,
        "error": None,
        "final_report": "",
    }
    return agent.invoke(initial_state)


def _run_query(
    planner: OrchestrationPlanner,
    *,
    query: str,
    top_k: int,
    max_retries: int,
    max_replans: int,
    parallel: bool,
    keep_context: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    planning_result = planner.create_plan(query, top_k=top_k, approval_required=True)
    execution_trace: list[dict[str, Any]] = [{"plan": planning_result.plan.model_dump(), "validation": planning_result.validation.model_dump()}]
    execution_result = _execute_approved_plan(
        planner,
        planning_result.plan,
        repo_root=planner.repo_root,
        max_retries=max_retries,
        parallel=parallel,
        keep_context=keep_context,
    )
    execution_trace.append({"execution": execution_result})

    current_plan = planning_result.plan
    replan_count = 0
    while execution_result.get("replan_request") and replan_count < max_replans:
        replan_count += 1
        planning_result = planner.create_plan(
            query,
            top_k=top_k,
            approval_required=False,
            previous_plan=current_plan,
            replan_reason=execution_result.get("replan_request"),
        )
        current_plan = planning_result.plan
        execution_trace.append({"plan": current_plan.model_dump(), "validation": planning_result.validation.model_dump()})
        execution_result = _execute_approved_plan(
            planner,
            current_plan,
            repo_root=planner.repo_root,
            max_retries=max_retries,
            parallel=parallel,
            keep_context=keep_context,
        )
        execution_trace.append({"execution": execution_result})

    return execution_trace, execution_result


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()
    parser = argparse.ArgumentParser(description="ai-config planning-first orchestrator")
    parser.add_argument("query", type=str, nargs="?", default="", help="User query")
    parser.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    parser.add_argument("--search-only", action="store_true", help="Run retriever only")
    parser.add_argument("--plan-only", action="store_true", help="Generate plan and stop before execution")
    parser.add_argument("--execute-plan", type=str, default="", help="Execute an approved plan from a JSON file path or JSON string")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum retries per approved-plan step")
    parser.add_argument("--max-replans", type=int, default=2, help="Maximum controlled replans for default query execution")
    parser.add_argument("--top-k", type=int, default=8, help="Retriever top-k")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel execution for independent approved-plan steps")
    parser.add_argument("--keep-context", action="store_true", help="Keep .dispatch/ context directory after execution")
    parser.add_argument("--trace", action="store_true", help="Print plan / execution trace JSON")
    args = parser.parse_args(argv)

    index_dir = args.index_dir.resolve()
    if not (index_dir / "summary.json").exists():
        logger.error("Index artifacts not found: %s. Run ai-config-index first.", index_dir)
        sys.exit(1)

    if args.search_only:
        if not args.query:
            parser.error("A query is required with --search-only.")
        _print_search_only(index_dir, args.query, args.top_k)
        return

    repo_root = Path(".").resolve()
    planner = OrchestrationPlanner(index_dir=index_dir, repo_root=repo_root)

    if args.execute_plan:
        plan = planner.load_plan_input(args.execute_plan)
        validation = validate_orchestration_plan(plan, planner.records_by_id)
        if not validation.valid:
            logger.error("Approved plan validation failed: %s", "; ".join(validation.errors))
            sys.exit(1)
        result = _execute_approved_plan(
            planner,
            plan,
            repo_root=repo_root,
            max_retries=args.max_retries,
            parallel=args.parallel,
            keep_context=args.keep_context,
        )
        if args.trace:
            print("TRACE:")
            print(json.dumps({"plan": plan.model_dump(), "execution": result}, ensure_ascii=False, indent=2, default=str))
            print("")
        print(result.get("final_report", "(no report)"))
        return

    if not args.query:
        parser.error("A query or --execute-plan is required.")

    planning_result = planner.create_plan(args.query, top_k=max(1, args.top_k), approval_required=True)
    if args.plan_only:
        print(render_plan_summary(planning_result.plan))
        print("")
        print("JSON:")
        print(json.dumps(planning_result.plan.model_dump(), ensure_ascii=False, indent=2, default=str))
        return

    trace, execution_result = _run_query(
        planner,
        query=args.query,
        top_k=max(1, args.top_k),
        max_retries=args.max_retries,
        max_replans=args.max_replans,
        parallel=args.parallel,
        keep_context=args.keep_context,
    )

    if args.trace:
        print("TRACE:")
        print(json.dumps(trace, ensure_ascii=False, indent=2, default=str))
        print("")

    print(execution_result.get("final_report", "(no report)"))


if __name__ == "__main__":
    main()
