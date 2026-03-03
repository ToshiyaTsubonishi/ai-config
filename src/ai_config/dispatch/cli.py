"""CLI entrypoint for multi-agent dispatch orchestrator."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from dotenv import load_dotenv

from ai_config.dispatch.graph import create_dispatch_agent
from ai_config.dispatch.planner import detect_available_agents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Multi-agent dispatch orchestrator for AI coding tools"
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
    args = parser.parse_args(argv)

    # --- List workflows ---
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

    if not args.prompt and not args.workflow:
        parser.error("A prompt or --workflow is required.")

    preferred = [a.strip() for a in args.agents.split(",") if a.strip()] if args.agents else []

    # Quick availability check
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

    report = result.get("final_report", "(no report)")
    print(report)


if __name__ == "__main__":
    main()
