"""CLI entrypoint for selector search, plan generation, and boundary execution."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from ai_config.contracts.approved_plan import (
    ApprovedPlan,
    ApprovedPlanExecutionRequest,
    approved_plan_execution_request_json_schema,
    approved_plan_json_schema,
)
from ai_config.executor import DispatchCLIPlanExecutor
from ai_config.orchestrator.planner import OrchestrationPlanner, render_plan_summary
from ai_config.orchestrator.validator import validate_orchestration_plan
from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.retriever.query_intent import infer_query_intent
from ai_config.runtime_env import load_runtime_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_SUBCOMMANDS = {"search", "plan", "execute-approved-plan", "run", "schema"}


def _print_search(index_dir: Path, query: str, top_k: int) -> None:
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


def _build_execution_request(
    planner: OrchestrationPlanner,
    plan: ApprovedPlan,
    *,
    repo_root: Path,
    max_retries: int,
    parallel: bool,
    keep_context: bool,
) -> ApprovedPlanExecutionRequest:
    resolved_records = [record.to_dict() for record in planner.resolve_records_for_plan(plan).values()]
    return ApprovedPlanExecutionRequest(
        plan=plan,
        repo_root=str(repo_root),
        working_directory=str(repo_root),
        tool_records=resolved_records,
        max_retries=max(0, max_retries),
        parallel=parallel,
        keep_context=keep_context,
    )


def _execute_approved_plan(
    planner: OrchestrationPlanner,
    plan: ApprovedPlan,
    *,
    repo_root: Path,
    max_retries: int,
    parallel: bool,
    keep_context: bool,
) -> tuple[ApprovedPlanExecutionRequest, dict[str, Any]]:
    request = _build_execution_request(
        planner,
        plan,
        repo_root=repo_root,
        max_retries=max_retries,
        parallel=parallel,
        keep_context=keep_context,
    )
    executor = DispatchCLIPlanExecutor(repo_root=repo_root)
    return request, executor.execute_request(request)


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
    request, execution_result = _execute_approved_plan(
        planner,
        planning_result.plan,
        repo_root=planner.repo_root,
        max_retries=max_retries,
        parallel=parallel,
        keep_context=keep_context,
    )
    execution_trace: list[dict[str, Any]] = [
        {"plan": planning_result.plan.model_dump(), "validation": planning_result.validation.model_dump()},
        {"execution_request": request.model_dump(), "execution": execution_result},
    ]

    current_plan = planning_result.plan
    replan_count = 0
    while execution_result.get("replan_request") and replan_count < max_replans:
        replan_count += 1
        planning_result = planner.controlled_replan(
            query,
            top_k=top_k,
            previous_plan=current_plan,
            replan_reason=execution_result.get("replan_request"),
        )
        current_plan = planning_result.plan
        request, execution_result = _execute_approved_plan(
            planner,
            current_plan,
            repo_root=planner.repo_root,
            max_retries=max_retries,
            parallel=parallel,
            keep_context=keep_context,
        )
        execution_trace.append({"plan": current_plan.model_dump(), "validation": planning_result.validation.model_dump()})
        execution_trace.append({"execution_request": request.model_dump(), "execution": execution_result})

    return execution_trace, execution_result


def _require_index(index_dir: Path) -> None:
    if not (index_dir / "summary.json").exists():
        logger.error("Index artifacts not found: %s. Run ai-config-index first.", index_dir)
        sys.exit(1)


def _planner_from(index_dir: Path) -> OrchestrationPlanner:
    _require_index(index_dir)
    repo_root = Path(".").resolve()
    return OrchestrationPlanner(index_dir=index_dir, repo_root=repo_root)


def _emit_execution_result(result: dict[str, Any]) -> None:
    if result.get("status") == "error":
        message = str(result.get("error") or result.get("final_report") or "(execution failed)")
        print(message)
        sys.exit(1)
    print(result.get("final_report", "(no report)"))


def _build_subcommand_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ai-config selector and planner CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Run selector retrieval only")
    search.add_argument("query", type=str, help="User query")
    search.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    search.add_argument("--top-k", type=int, default=8, help="Retriever top-k")

    plan = subparsers.add_parser("plan", help="Generate an approved plan artifact")
    plan.add_argument("query", type=str, help="User query")
    plan.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    plan.add_argument("--top-k", type=int, default=8, help="Retriever top-k")

    execute = subparsers.add_parser(
        "execute-approved-plan",
        help="Execute an approved plan through the stable dispatch boundary",
    )
    execute.add_argument("--plan", required=True, help="Approved plan JSON file path or JSON string")
    execute.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    execute.add_argument("--max-retries", type=int, default=2, help="Maximum retries per approved-plan step")
    execute.add_argument("--parallel", action="store_true", help="Enable parallel execution for independent approved-plan steps")
    execute.add_argument("--keep-context", action="store_true", help="Keep .dispatch/ context directory after execution")
    execute.add_argument("--trace", action="store_true", help="Print plan / execution trace JSON")

    run = subparsers.add_parser(
        "run",
        help="Generate a plan and execute it through the stable dispatch boundary",
    )
    run.add_argument("query", type=str, help="User query")
    run.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    run.add_argument("--top-k", type=int, default=8, help="Retriever top-k")
    run.add_argument("--max-retries", type=int, default=2, help="Maximum retries per approved-plan step")
    run.add_argument("--max-replans", type=int, default=2, help="Maximum controlled replans")
    run.add_argument("--parallel", action="store_true", help="Enable parallel execution for independent approved-plan steps")
    run.add_argument("--keep-context", action="store_true", help="Keep .dispatch/ context directory after execution")
    run.add_argument("--trace", action="store_true", help="Print plan / execution trace JSON")

    schema = subparsers.add_parser("schema", help="Print stable contract JSON schema")
    schema.add_argument(
        "kind",
        choices=("approved-plan", "approved-plan-execution-request"),
        help="Contract schema to print",
    )

    return parser


def _run_subcommand(argv: list[str]) -> None:
    parser = _build_subcommand_parser()
    args = parser.parse_args(argv)

    if args.command == "schema":
        schema = approved_plan_json_schema() if args.kind == "approved-plan" else approved_plan_execution_request_json_schema()
        print(json.dumps(schema, ensure_ascii=False, indent=2))
        return

    index_dir = args.index_dir.resolve()

    if args.command == "search":
        _require_index(index_dir)
        _print_search(index_dir, args.query, max(1, args.top_k))
        return

    planner = _planner_from(index_dir)

    if args.command == "plan":
        planning_result = planner.create_plan(args.query, top_k=max(1, args.top_k), approval_required=True)
        print(render_plan_summary(planning_result.plan))
        print("")
        print("JSON:")
        print(json.dumps(planning_result.plan.model_dump(), ensure_ascii=False, indent=2, default=str))
        return

    if args.command == "execute-approved-plan":
        plan = planner.load_plan_input(args.plan)
        validation = planner.validate_plan_artifact(plan)
        if not validation.valid:
            logger.error("Approved plan validation failed: %s", "; ".join(validation.errors))
            sys.exit(1)
        request, result = _execute_approved_plan(
            planner,
            plan,
            repo_root=planner.repo_root,
            max_retries=args.max_retries,
            parallel=args.parallel,
            keep_context=args.keep_context,
        )
        if args.trace:
            print("TRACE:")
            print(json.dumps({"execution_request": request.model_dump(), "execution": result}, ensure_ascii=False, indent=2, default=str))
            print("")
        _emit_execution_result(result)
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
    _emit_execution_result(execution_result)


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ai-config legacy compatibility CLI")
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
    return parser


def _run_legacy(argv: list[str]) -> None:
    parser = _build_legacy_parser()
    args = parser.parse_args(argv)
    index_dir = args.index_dir.resolve()

    if args.search_only:
        if not args.query:
            parser.error("A query is required with --search-only.")
        _require_index(index_dir)
        _print_search(index_dir, args.query, max(1, args.top_k))
        return

    planner = _planner_from(index_dir)

    if args.execute_plan:
        plan = planner.load_plan_input(args.execute_plan)
        validation = validate_orchestration_plan(plan, planner.records_by_id)
        if not validation.valid:
            logger.error("Approved plan validation failed: %s", "; ".join(validation.errors))
            sys.exit(1)
        request, result = _execute_approved_plan(
            planner,
            plan,
            repo_root=planner.repo_root,
            max_retries=args.max_retries,
            parallel=args.parallel,
            keep_context=args.keep_context,
        )
        if args.trace:
            print("TRACE:")
            print(json.dumps({"execution_request": request.model_dump(), "execution": result}, ensure_ascii=False, indent=2, default=str))
            print("")
        _emit_execution_result(result)
        return

    if not args.query:
        parser.error("A query or --execute-plan is required.")

    if args.plan_only:
        planning_result = planner.create_plan(args.query, top_k=max(1, args.top_k), approval_required=True)
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
    _emit_execution_result(execution_result)


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()
    args = list(argv or sys.argv[1:])
    if not args:
        _run_subcommand(["-h"])
        return
    if args[0] in {"-h", "--help"} or args[0] in _SUBCOMMANDS:
        _run_subcommand(args)
        return
    _run_legacy(args)


if __name__ == "__main__":
    main()
