"""Dispatcher – invokes CLI agents as subprocesses for each TaskStep.

Supports both sequential and parallel dispatch modes.
Handles file-based context handoff between steps.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ai_config.dispatch.planner import AGENT_PROFILES
from ai_config.executor import ToolExecutor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variable safety
# ---------------------------------------------------------------------------
_SAFE_ENV_KEYS = {
    "PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL", "LC_CTYPE",
    "TERM", "TMPDIR", "TMP", "TEMP",
    # Agent-specific overrides
    "AI_CONFIG_GEMINI_CMD", "AI_CONFIG_CODEX_CMD", "AI_CONFIG_ANTIGRAVITY_CMD",
    # Required for LLM API access (agents need these)
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY",
    # Node / Python runtime
    "NODE_PATH", "PYTHONPATH", "VIRTUAL_ENV",
}


def _build_safe_env() -> dict[str, str]:
    """Build a filtered environment dict containing only safe keys."""
    return {k: v for k, v in os.environ.items() if k in _SAFE_ENV_KEYS}


# ---------------------------------------------------------------------------
# Context directory management
# ---------------------------------------------------------------------------
def _ensure_context_dir(state: dict[str, Any]) -> Path:
    """Get or create a shared context directory for this dispatch session."""
    ctx_dir = state.get("context_dir")
    if ctx_dir:
        path = Path(ctx_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    session_id = state.get("session_id", uuid.uuid4().hex[:8])
    working_dir = state.get("working_directory", ".")
    path = Path(working_dir) / ".dispatch" / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_step_context(
    context_dir: Path, step_id: str, result: dict[str, Any]
) -> None:
    """Save a step's output to the context directory for downstream steps."""
    output = result.get("output", "")
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False, default=str)
    ctx_file = context_dir / f"{step_id}.json"
    ctx_file.write_text(
        json.dumps(
            {
                "step_id": step_id,
                "agent": result.get("agent", ""),
                "status": result.get("status", ""),
                "output_summary": output[:3000],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_context_for_step(
    context_dir: Path, depends_on: list[str]
) -> str:
    """Load context from dependency steps to inject into the prompt."""
    if not depends_on:
        return ""

    context_parts: list[str] = []
    for dep_id in depends_on:
        ctx_file = context_dir / f"{dep_id}.json"
        if ctx_file.exists():
            try:
                data = json.loads(ctx_file.read_text(encoding="utf-8"))
                summary = data.get("output_summary", "")[:1000]
                if summary:
                    context_parts.append(
                        f"[Previous step {dep_id} output]:\n{summary}"
                    )
            except Exception:
                pass

    if not context_parts:
        return ""

    return (
        "\n\n--- Context from previous steps ---\n"
        + "\n\n".join(context_parts)
        + "\n--- End context ---\n"
    )


# ---------------------------------------------------------------------------
# CLI command builders
# ---------------------------------------------------------------------------
def _build_cli_command(agent: str, prompt: str) -> list[str]:
    """Build the subprocess command for a given agent and prompt."""
    profile = AGENT_PROFILES.get(agent, {})
    cmd = os.getenv(profile.get("env_var", ""), profile.get("command", agent))

    if agent == "gemini":
        # -p takes prompt as string value, --yolo auto-approves all actions
        return [cmd, "-p", prompt, "--yolo"]
    elif agent == "codex":
        # exec subcommand, --full-auto for sandboxed autonomous execution
        return [cmd, "exec", prompt, "--full-auto"]
    elif agent == "antigravity":
        return [cmd, "--prompt", prompt]
    else:
        return [cmd, prompt]


def _run_agent(
    agent: str,
    prompt: str,
    working_directory: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run a CLI agent as a subprocess and capture output."""
    command = _build_cli_command(agent, prompt)
    cmd_name = command[0]

    if shutil.which(cmd_name) is None:
        return {
            "status": "error",
            "error": f"CLI not found: {cmd_name}",
            "output": "",
        }

    cwd = os.path.abspath(working_directory)
    logger.info(
        "Dispatching to %s (timeout=%ds, cwd=%s): %s",
        agent,
        timeout_seconds,
        cwd,
        prompt[:100],
    )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=cwd,
            env=_build_safe_env(),
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr if result.stderr else "",
            }
        else:
            return {
                "status": "error",
                "output": result.stdout,
                "error": result.stderr or f"Exit code: {result.returncode}",
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "output": "",
            "error": f"Agent {agent} timed out after {timeout_seconds}s",
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e),
        }


def _run_tool_step(step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(state.get("repo_root") or state.get("working_directory", ".")).resolve()
    executor = ToolExecutor(repo_root=repo_root)
    tool_records = state.get("tool_records", [])
    if isinstance(tool_records, list):
        executor.register_records(tool_records)

    tool_id = str(step.get("tool_id", ""))
    action = str(step.get("action", "run"))
    params = dict(step.get("params", {}) or {})
    working_directory = str(step.get("working_directory", state.get("working_directory", ".")))
    return executor.tools_call(tool_id=tool_id, action=action, params=params, cwd=working_directory)


def _execute_step_payload(
    step: dict[str, Any],
    state: dict[str, Any],
    context_dir: Path | None,
    *,
    retry_count: int = 0,
) -> dict[str, Any]:
    execution_backend = str(step.get("execution_backend", "agent"))
    step_id = step.get("step_id", "step-unknown")

    if execution_backend == "tool":
        run_result = _run_tool_step(step, state)
        error_payload = run_result.get("error")
        error_text = ""
        if error_payload:
            if isinstance(error_payload, dict):
                error_text = str(error_payload.get("message", ""))[:1000]
            else:
                error_text = str(error_payload)[:1000]

        entry = {
            "step_id": step_id,
            "agent": "tool_executor",
            "tool_id": step.get("tool_id", ""),
            "action": step.get("action", "run"),
            "status": run_result.get("status", "error"),
            "output": run_result.get("output"),
            "error": error_text,
            "error_details": error_payload,
            "retry_count": retry_count,
        }
        if context_dir and entry["status"] == "success":
            _save_step_context(context_dir, step_id, entry)
        return entry

    agent = step.get("agent", "gemini")
    prompt = step.get("prompt", "")
    working_dir = step.get("working_directory", state.get("working_directory", "."))
    timeout = step.get("timeout_seconds", 300)

    if context_dir:
        deps = step.get("depends_on", [])
        context_text = _load_context_for_step(context_dir, deps)
        if context_text:
            prompt = prompt + context_text

    run_result = _run_agent(agent, prompt, working_dir, timeout)
    entry = {
        "step_id": step_id,
        "agent": agent,
        "status": run_result["status"],
        "output": run_result["output"][:2000],
        "error": run_result["error"][:1000] if run_result.get("error") else "",
        "retry_count": retry_count,
    }
    if context_dir and run_result["status"] == "success":
        _save_step_context(context_dir, step_id, entry)
    return entry


# ---------------------------------------------------------------------------
# Parallel dispatch helpers
# ---------------------------------------------------------------------------
def _find_parallel_batch(
    plan: list[dict[str, Any]],
    current_step: int,
    completed_ids: set[str],
) -> list[int]:
    """Find steps starting from current_step that can run in parallel.

    A step is eligible if all its dependencies are in completed_ids.
    We collect a batch of consecutive eligible steps until we hit one
    whose dependencies are unmet.
    """
    batch: list[int] = []
    for idx in range(current_step, len(plan)):
        step = plan[idx]
        depends_on = step.get("depends_on", [])
        if all(dep in completed_ids for dep in depends_on):
            batch.append(idx)
        else:
            # Skip steps with unmet deps (they'll wait for their dependencies)
            continue
    return batch if len(batch) > 1 else []


def _execute_parallel_batch(
    plan: list[dict[str, Any]],
    indices: list[int],
    state: dict[str, Any],
    context_dir: Path | None,
) -> list[dict[str, Any]]:
    """Execute multiple steps concurrently using ThreadPoolExecutor."""
    results: list[dict[str, Any]] = [None] * len(indices)  # type: ignore

    def _run_one(batch_pos: int, step_idx: int) -> None:
        step = plan[step_idx]
        step_id = step.get("step_id", f"step-{step_idx + 1}")
        logger.info(
            "=== Parallel Step %s: [%s] %s ===",
            step_idx + 1,
            step.get("agent", step.get("tool_id", "tool_executor")),
            step_id,
        )
        results[batch_pos] = _execute_step_payload(step, state, context_dir, retry_count=0)

    max_workers = min(len(indices), 4)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_run_one, i, idx): i
            for i, idx in enumerate(indices)
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                pos = futures[future]
                step_idx = indices[pos]
                step = plan[step_idx]
                results[pos] = {
                    "step_id": step.get("step_id", f"step-{step_idx + 1}"),
                    "agent": step.get("agent", "?"),
                    "status": "error",
                    "output": "",
                    "error": str(e),
                    "retry_count": 0,
                }

    return results  # type: ignore


# ---------------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------------
def dispatch_step(state: dict[str, Any]) -> dict[str, Any]:
    """Execute the current step (or parallel batch) by dispatching to CLI agents."""
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    parallel_enabled = state.get("parallel", False)

    if current_step >= len(plan):
        return {"done": True}

    # Setup context directory
    context_dir: Path | None = None
    session_id = state.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex[:8]

    context_dir = _ensure_context_dir(
        {**state, "session_id": session_id}
    )

    # Check for parallel batch
    if parallel_enabled:
        past_results = state.get("step_results", [])
        completed_ids = {
            r["step_id"] for r in past_results if r.get("status") == "success"
        }
        batch = _find_parallel_batch(plan, current_step, completed_ids)

        if batch:
            logger.info(
                "Parallel batch: dispatching steps %s concurrently",
                [plan[i].get("step_id", f"step-{i+1}") for i in batch],
            )
            batch_results = _execute_parallel_batch(
                plan, batch, state, context_dir
            )
            results = list(past_results)
            results.extend(batch_results)

            last_result = batch_results[-1] if batch_results else None
            new_step = max(batch) + 1

            return {
                "step_results": results,
                "last_step_result": last_result,
                "current_step": new_step,
                "session_id": session_id,
                "context_dir": str(context_dir),
            }

    # --- Sequential dispatch (single step) ---
    step = plan[current_step]
    step_id = step.get("step_id", f"step-{current_step + 1}")
    agent = step.get("agent", step.get("tool_id", "tool_executor"))

    # Check dependencies
    depends_on = step.get("depends_on", [])
    if depends_on:
        past_results = state.get("step_results", [])
        completed_ids = {
            r["step_id"]
            for r in past_results
            if r.get("status") == "success"
        }
        unmet = [dep for dep in depends_on if dep not in completed_ids]
        if unmet:
            result_entry = {
                "step_id": step_id,
                "agent": agent,
                "status": "skipped",
                "output": "",
                "error": f"Unmet dependencies: {', '.join(unmet)}",
                "retry_count": 0,
            }
            results = list(state.get("step_results", []))
            results.append(result_entry)
            return {
                "step_results": results,
                "current_step": current_step + 1,
                "step_retry_count": 0,
                "session_id": session_id,
                "context_dir": str(context_dir),
            }

    # Inject context from dependency steps
    logger.info("=== Step %d/%d: [%s] %s ===", current_step + 1, len(plan), agent, step_id)
    retry_count = state.get("step_retry_count", 0)
    result_entry = _execute_step_payload(step, state, context_dir, retry_count=retry_count)

    results = list(state.get("step_results", []))
    results.append(result_entry)

    return {
        "step_results": results,
        "last_step_result": result_entry,
        "current_step": current_step,  # explicit for consistency with parallel path
        "session_id": session_id,
        "context_dir": str(context_dir),
    }
