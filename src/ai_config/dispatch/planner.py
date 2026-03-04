"""Task planner – decomposes user prompts into executable steps via LLM."""

from __future__ import annotations

import functools
import json
import logging
import os
import shutil
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent capability descriptions (used in the planning prompt)
# ---------------------------------------------------------------------------
AGENT_PROFILES: dict[str, dict[str, str]] = {
    "gemini": {
        "command": "gemini",
        "env_var": "AI_CONFIG_GEMINI_CMD",
        "strengths": (
            "Research, code generation, file operations, large-scale refactoring, "
            "project-wide analysis. Supports --sandbox permissive for file writes."
        ),
    },
    "codex": {
        "command": "codex",
        "env_var": "AI_CONFIG_CODEX_CMD",
        "strengths": (
            "Code implementation, test execution, sandboxed changes, "
            "bug fixes. Runs with --approval full-auto for autonomous execution."
        ),
    },
    "antigravity": {
        "command": "antigravity",
        "env_var": "AI_CONFIG_ANTIGRAVITY_CMD",
        "strengths": (
            "VSCode IDE integration, browser operations, UI verification, "
            "screenshot capture. Best for tasks requiring visual confirmation."
        ),
    },
}


def detect_available_agents(preferred: list[str] | None = None) -> list[str]:
    """Return list of agent names whose CLI binaries are available."""
    available: list[str] = []
    for name, profile in AGENT_PROFILES.items():
        cmd = os.getenv(profile["env_var"], profile["command"])
        if shutil.which(cmd) is not None:
            available.append(name)

    if preferred:
        # Filter to preferred agents that are actually available
        filtered = [a for a in preferred if a in available]
        if filtered:
            return filtered
        logger.warning(
            "Preferred agents %s not available, falling back to: %s",
            preferred,
            available,
        )

    return available


# ---------------------------------------------------------------------------
# Planning prompt template
# ---------------------------------------------------------------------------
_PLAN_PROMPT = """\
あなたは開発タスクを分解するプランナーです。
ユーザーの要求を、複数の独立した開発ステップに分解してください。

# ユーザー要求
{user_prompt}

# 利用可能なエージェント
{agent_descriptions}

# 作業ディレクトリ
{working_directory}

# ルール
- 各ステップは1つのエージェントに割り当てる
- ステップ間の依存関係がある場合は depends_on で明示する
- 各ステップの prompt には、そのステップで具体的に何をすべきか詳細に記述する
- prompt はエージェントがそのまま実行できる自己完結した指示にする
- 前のステップの結果に依存する場合は、作業ディレクトリ内のファイルを介して連携する前提で記述する
- 適切なエージェントを選ぶ（得意分野を考慮する）
- 並列実行可能なステップは depends_on を空にする
- timeout_seconds はタスクの複雑さに応じて 60〜600 の範囲で設定する

# 返却 JSON 形式（JSON のみ返してください）
{{
  "steps": [
    {{
      "step_id": "step-1",
      "description": "このステップの概要",
      "agent": "gemini|codex|antigravity",
      "prompt": "エージェントへの詳細な指示",
      "depends_on": [],
      "working_directory": ".",
      "timeout_seconds": 300
    }}
  ],
  "summary": "全体の計画概要"
}}
"""


def _format_agent_descriptions(available: list[str]) -> str:
    """Format agent profiles into a human-readable description."""
    lines: list[str] = []
    for name in available:
        profile = AGENT_PROFILES.get(name, {})
        strengths = profile.get("strengths", "General purpose")
        lines.append(f"- **{name}**: {strengths}")
    return "\n".join(lines)


def _parse_plan_json(raw: str) -> dict[str, Any]:
    """Extract JSON from LLM response, handling markdown fences."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1 :]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return json.loads(text.strip())


def _extract_text(response: Any) -> str:
    """Safely extract text content from an LLM response.

    Handles cases where response.content is a list (multi-part)
    instead of a plain string.
    """
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, list):
        # Multi-part content: join text parts
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(part.text)
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def _fallback_single_step(
    user_prompt: str, available_agents: list[str], working_directory: str
) -> dict[str, Any]:
    """Create a simple single-step plan when LLM planning fails."""
    agent = available_agents[0] if available_agents else "gemini"
    return {
        "steps": [
            {
                "step_id": "step-1",
                "description": "Execute user request directly",
                "agent": agent,
                "prompt": user_prompt,
                "depends_on": [],
                "working_directory": working_directory,
                "timeout_seconds": 300,
            }
        ],
        "summary": f"Fallback: direct execution via {agent}",
    }


# ---------------------------------------------------------------------------
# LangGraph node functions
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _get_llm():
    """Lazy-init the LLM for planning (cached, thread-safe via lru_cache)."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        return ChatGoogleGenerativeAI(model=model, temperature=0.2)
    except Exception as e:
        logger.error("Failed to initialise planning LLM: %s", e)
        return None


def plan_tasks(state: dict[str, Any]) -> dict[str, Any]:
    """Decompose user prompt into TaskSteps via LLM, or load from workflow."""
    user_prompt: str = state["user_prompt"]
    working_directory: str = state.get("working_directory", ".")
    preferred: list[str] = state.get("preferred_agents", [])
    dry_run: bool = state.get("dry_run", False)
    workflow_name: str = state.get("workflow_name", "")

    available = detect_available_agents(preferred or None)
    if not available:
        return {
            "plan": [],
            "available_agents": [],
            "done": True,
            "error": "No CLI agents available. Install gemini, codex, or antigravity.",
            "final_report": "Error: No CLI agents available.",
        }

    # --- Workflow-based planning ---
    if workflow_name:
        from ai_config.dispatch.workflow import load_workflow, render_workflow_steps

        wf = load_workflow(workflow_name)
        if wf is not None:
            steps = render_workflow_steps(wf, user_prompt)
            # Validate agents
            for step in steps:
                if step.get("agent") not in available:
                    step["agent"] = available[0]

            result: dict[str, Any] = {
                "plan": steps,
                "available_agents": available,
                "current_step": 0,
                "total_steps": len(steps),
                "step_results": [],
                "step_retry_count": 0,
                "needs_replanning": False,
            }
            if dry_run:
                report_lines = [
                    f"=== Dispatch Plan (dry-run, workflow: {workflow_name}) ===",
                    f"Description: {wf.get('description', '')}",
                    "",
                ]
                for i, step in enumerate(steps, 1):
                    report_lines.append(
                        f"Step {i}: [{step['agent']}] {step.get('description', '')}"
                    )
                    deps = step.get("depends_on", [])
                    if deps:
                        report_lines.append(f"  depends_on: {', '.join(deps)}")
                    report_lines.append(f"  timeout: {step.get('timeout_seconds', 300)}s")
                    report_lines.append("")
                result["done"] = True
                result["final_report"] = "\n".join(report_lines)
            return result
        else:
            logger.warning("Workflow '%s' not found, falling back to LLM planning", workflow_name)

    # --- LLM-based planning ---
    llm = _get_llm()
    if llm is None:
        plan_data = _fallback_single_step(user_prompt, available, working_directory)
    else:
        prompt_text = _PLAN_PROMPT.format(
            user_prompt=user_prompt,
            agent_descriptions=_format_agent_descriptions(available),
            working_directory=working_directory,
        )
        try:
            response = llm.invoke(prompt_text)
            plan_data = _parse_plan_json(_extract_text(response))
        except Exception as e:
            logger.warning("LLM planning failed (%s), using fallback", e)
            plan_data = _fallback_single_step(user_prompt, available, working_directory)

    steps = plan_data.get("steps", [])

    # Validate agent assignments against available agents
    for step in steps:
        if step.get("agent") not in available:
            step["agent"] = available[0]

    result = {
        "plan": steps,
        "available_agents": available,
        "current_step": 0,
        "total_steps": len(steps),
        "step_results": [],
        "step_retry_count": 0,
        "needs_replanning": False,
    }

    if dry_run:
        summary = plan_data.get("summary", "")
        report_lines = [f"=== Dispatch Plan (dry-run) ===", f"Summary: {summary}", ""]
        for i, step in enumerate(steps, 1):
            report_lines.append(
                f"Step {i}: [{step['agent']}] {step.get('description', '')}"
            )
            deps = step.get("depends_on", [])
            if deps:
                report_lines.append(f"  depends_on: {', '.join(deps)}")
            report_lines.append(f"  timeout: {step.get('timeout_seconds', 300)}s")
            report_lines.append("")
        result["done"] = True
        result["final_report"] = "\n".join(report_lines)

    return result


def replan_tasks(state: dict[str, Any]) -> dict[str, Any]:
    """Re-plan remaining steps after a failure."""
    replan_count = state.get("replan_count", 0) + 1
    max_replans = state.get("max_replans", 2)

    if replan_count > max_replans:
        return {
            "done": True,
            "abort": True,
            "replan_count": replan_count,
            "final_report": "Aborted: exceeded maximum replan attempts.",
        }

    user_prompt = state["user_prompt"]
    available = state.get("available_agents", [])
    working_directory = state.get("working_directory", ".")
    past_results = state.get("step_results", [])

    # Build context from past results for replanning
    context_lines = ["Previous execution results:"]
    for r in past_results:
        status = r.get("status", "unknown")
        context_lines.append(
            f"- {r.get('step_id', '?')} [{r.get('agent', '?')}]: {status}"
        )
        if status == "error" and r.get("error"):
            context_lines.append(f"  Error: {r['error'][:200]}")

    augmented_prompt = (
        f"{user_prompt}\n\n"
        f"NOTE: A previous attempt partially failed. "
        f"Please create a revised plan that addresses the failures.\n"
        f"{chr(10).join(context_lines)}"
    )

    llm = _get_llm()
    if llm is None:
        plan_data = _fallback_single_step(augmented_prompt, available, working_directory)
    else:
        prompt_text = _PLAN_PROMPT.format(
            user_prompt=augmented_prompt,
            agent_descriptions=_format_agent_descriptions(available),
            working_directory=working_directory,
        )
        try:
            response = llm.invoke(prompt_text)
            plan_data = _parse_plan_json(_extract_text(response))
        except Exception as e:
            logger.warning("LLM re-planning failed (%s), using fallback", e)
            plan_data = _fallback_single_step(
                augmented_prompt, available, working_directory
            )

    steps = plan_data.get("steps", [])
    for step in steps:
        if step.get("agent") not in available:
            step["agent"] = available[0]

    return {
        "plan": steps,
        "current_step": 0,
        "total_steps": len(steps),
        "step_results": [],  # reset to prevent stale results from old plan
        "step_retry_count": 0,
        "needs_replanning": False,
        "replan_count": replan_count,
    }
