"""CLI entrypoint for dispatch runtime execution."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any
from uuid import uuid4

from ai_config.contracts.approved_plan import (
    ApprovedPlanExecutionRequest,
    ApprovedPlanExecutionResult,
    ApprovedPlanExecutionRuntime,
    load_approved_plan_execution_request,
)
from ai_config.dispatch.graph import create_dispatch_agent
from ai_config.dispatch.planner import detect_available_agents
from ai_config.runtime_env import load_runtime_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _result_payload(result: dict[str, object]) -> dict[str, object]:
    return {
        "status": "error" if result.get("error") else "success",
        "final_report": result.get("final_report", ""),
        "error": result.get("error"),
        "step_results": result.get("step_results", []),
        "replan_request": result.get("replan_request"),
    }


def _approved_plan_status(result: dict[str, Any]) -> str:
    if result.get("abort"):
        return "aborted"
    if result.get("error"):
        return "error"
    if result.get("replan_request") is not None:
        return "partial"
    return "success"


def _step_output_summary(raw_step: dict[str, Any]) -> str:
    output = raw_step.get("output")
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    return json.dumps(output, ensure_ascii=False, default=str)


def _approved_plan_result_payload(
    request: ApprovedPlanExecutionRequest,
    result: dict[str, Any],
) -> dict[str, Any]:
    status = _approved_plan_status(result)
    top_level_error = None
    if status in {"error", "aborted"}:
        top_level_error = str(result.get("error") or result.get("final_report") or "dispatch runtime failure")

    payload = ApprovedPlanExecutionResult(
        request_kind=request.kind,
        request_schema_version=request.schema_version,
        plan_id=request.plan.plan_id,
        plan_revision=request.plan.revision,
        execution_id=str(result.get("execution_id") or f"exec-{uuid4().hex[:10]}"),
        runtime=ApprovedPlanExecutionRuntime(name="ai-config-dispatch"),
        status=status,
        final_report=str(result.get("final_report") or ""),
        step_results=[
            {
                "step_id": str(
                    raw_step.get("step_id")
                    or raw_step.get("id")
                    or (raw_step.get("step", {}) if isinstance(raw_step.get("step"), dict) else {}).get("step_id")
                    or ""
                ),
                "status": str(raw_step.get("status") or ("error" if raw_step.get("error") else "success")),
                "agent": str(raw_step.get("agent") or ""),
                "tool_id": str(raw_step.get("tool_id") or raw_step.get("tool", "") or ""),
                "action": str(raw_step.get("action") or ""),
                "retry_count": int(raw_step.get("retry_count", raw_step.get("retry_attempt", raw_step.get("retries", 0))) or 0),
                "output_summary": str(raw_step.get("output_summary") or _step_output_summary(raw_step)),
                "error": raw_step.get("error"),
            }
            for raw_step in (result.get("step_results") or [])
            if isinstance(raw_step, dict)
        ],
        replan_request=result.get("replan_request") if status == "partial" else None,
        error=top_level_error,
    )
    return payload.model_dump()


def _print_result(result: dict[str, object], *, json_output: bool) -> None:
    payload = _result_payload(result)
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    report = str(payload.get("final_report") or "(no report)")
    print(report)


def _initial_state_from_request(request_path_or_json: ApprovedPlanExecutionRequest | str) -> dict[str, object]:
    request = (
        request_path_or_json
        if isinstance(request_path_or_json, ApprovedPlanExecutionRequest)
        else load_approved_plan_execution_request(request_path_or_json)
    )
    return {
        "user_prompt": request.plan.user_goal,
        "working_directory": request.working_directory,
        "repo_root": request.repo_root,
        "approved_plan": request.plan.model_dump(),
        "tool_records": request.tool_records,
        "max_retries": request.max_retries,
        "max_replans": 0,
        "dry_run": False,
        "parallel": request.parallel,
        "keep_context": request.keep_context,
        "step_results": [],
        "replan_count": 0,
        "replan_request": None,
        "done": False,
        "abort": False,
        "needs_replanning": False,
        "error": None,
        "final_report": "",
    }


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()

    parser = argparse.ArgumentParser(
        description="Dispatch runtime for AI coding tools"
    )
    parser.add_argument("prompt", type=str, nargs="?", default="",
                        help="Development task to dispatch")
    parser.add_argument(
        "--agents",
        type=str,
        default="",
        help="Comma-separated list of preferred agents (gemini,codex,antigravity)",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=".",
        help="Working directory for agents",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum retries per step (default: 2)",
    )
    parser.add_argument(
        "--max-replans",
        type=int,
        default=2,
        help="Maximum replanning attempts (default: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the plan without executing",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel dispatch for independent steps",
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default="",
        help="Name of a predefined workflow to use instead of LLM planning",
    )
    parser.add_argument(
        "--list-workflows",
        action="store_true",
        help="List available workflow definitions",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print full execution trace as JSON",
    )
    parser.add_argument(
        "--keep-context",
        action="store_true",
        help="Keep .dispatch/ context directory after execution",
    )
    parser.add_argument(
        "--execute-approved-plan",
        type=str,
        default="",
        help="Stable approved-plan execution request as JSON file path or JSON string",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON result",
    )
    args = parser.parse_args(argv)

    if args.list_workflows:
        from ai_config.dispatch.workflow import list_workflows

        workflows = list_workflows()
        if not workflows:
            print("No workflows found.")
        else:
            print("Available workflows:")
            for wf in workflows:
                print(f"  {wf['name']:20s} {wf.get('description', '')}")
                print(f"    Steps: {wf['steps']}  Path: {wf['path']}")
        return

    if args.execute_approved_plan:
        request = load_approved_plan_execution_request(args.execute_approved_plan)
        agent = create_dispatch_agent()
        result = agent.invoke(_initial_state_from_request(request))
        if args.trace:
            print("\nTRACE:")
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            print()
        payload = _approved_plan_result_payload(request, result)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        else:
            print(payload.get("final_report") or "(no report)")
        if payload.get("status") in {"error", "aborted"}:
            sys.exit(1)
        return

    if not args.prompt and not args.workflow:
        parser.error("A prompt or --workflow is required.")

    preferred = [a.strip() for a in args.agents.split(",") if a.strip()] if args.agents else []
    available = detect_available_agents(preferred or None)
    if not available and not args.dry_run:
        logger.error(
            "No CLI agents found. Install at least one of: gemini, codex, antigravity"
        )
        sys.exit(1)

    if available:
        logger.info("Available agents: %s", ", ".join(available))
    if args.parallel:
        logger.info("Parallel dispatch: ENABLED")

    agent = create_dispatch_agent()
    initial_state = {
        "user_prompt": args.prompt or f"Execute workflow: {args.workflow}",
        "working_directory": args.cwd,
        "preferred_agents": preferred,
        "max_retries": max(0, args.max_retries),
        "max_replans": max(0, args.max_replans),
        "dry_run": args.dry_run,
        "parallel": args.parallel,
        "workflow_name": args.workflow,
        "keep_context": args.keep_context,
        "step_results": [],
        "replan_count": 0,
        "done": False,
        "abort": False,
        "needs_replanning": False,
        "error": None,
        "final_report": "",
    }

    result = agent.invoke(initial_state)

    if args.trace:
        print("\nTRACE:")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        print()

    _print_result(result, json_output=args.json)
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
