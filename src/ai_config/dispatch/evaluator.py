"""Evaluator – assesses step results and decides next action."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def evaluate_step(state: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the result of the last dispatched step.

    Decides whether to:
    - advance to the next step (success)
    - retry the current step or switch agent (recoverable error)
    - trigger replanning (fundamental failure)
    - finalize (all steps done)
    """
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    step_results = state.get("step_results", [])
    max_retries = state.get("max_retries", 2)
    retry_count = state.get("step_retry_count", 0)
    available_agents = state.get("available_agents", [])
    approved_plan = state.get("approved_plan")

    if not step_results:
        return {"done": True, "error": "No step results to evaluate"}

    if approved_plan:
        return _evaluate_approved_plan_step(state, plan, current_step, step_results, max_retries, retry_count)

    # Check if current_step is already past the plan (e.g. after parallel batch)
    if current_step >= len(plan):
        # All steps dispatched. Check if any failed.
        failed = [r for r in step_results if r.get("status") not in ("success", "skipped")]
        if not failed:
            return {"done": True, "step_retry_count": 0}
        # Find the first failed step and set up for retry
        first_fail = failed[0]
        fail_step_id = first_fail.get("step_id", "")
        fail_idx = next(
            (i for i, s in enumerate(plan) if s.get("step_id") == fail_step_id),
            None,
        )
        if fail_idx is not None and retry_count < max_retries:
            current_agent = first_fail.get("agent", "")
            alternative = _pick_alternative_agent(current_agent, available_agents)
            if alternative and alternative != current_agent:
                logger.info(
                    "Step %s failed with %s, trying %s (retry %d/%d)",
                    fail_step_id, current_agent, alternative,
                    retry_count + 1, max_retries,
                )
                plan_copy = [dict(s) for s in plan]
                plan_copy[fail_idx]["agent"] = alternative
                # Remove previous failed results for this step so it can be re-dispatched
                clean_results = [r for r in step_results if r.get("step_id") != fail_step_id]
                return {
                    "plan": plan_copy,
                    "current_step": fail_idx,
                    "step_results": clean_results,
                    "step_retry_count": retry_count + 1,
                    "needs_replanning": False,
                }
        # Exceeded retries or can't find step → trigger replan or finalize
        if retry_count >= max_retries:
            return {"needs_replanning": True, "step_retry_count": 0}
        return {"done": True}

    last_result = step_results[-1]
    status = last_result.get("status", "error")

    if status == "success" or status == "skipped":
        # Advance to next step
        next_step = current_step + 1
        if next_step >= len(plan):
            return {"current_step": next_step, "done": True, "step_retry_count": 0}
        return {
            "current_step": next_step,
            "step_retry_count": 0,
            "needs_replanning": False,
        }

    # --- Failure handling ---
    if retry_count < max_retries:
        # Try again, possibly with a different agent
        current_agent = last_result.get("agent", "")
        alternative = _pick_alternative_agent(
            current_agent, available_agents
        )

        if alternative and alternative != current_agent:
            # Switch to an alternative agent for this step
            logger.info(
                "Step %s failed with %s, trying %s (retry %d/%d)",
                last_result.get("step_id", "?"),
                current_agent,
                alternative,
                retry_count + 1,
                max_retries,
            )
            # Update the plan to use the alternative agent
            plan_copy = [dict(s) for s in plan]
            plan_copy[current_step]["agent"] = alternative
            return {
                "plan": plan_copy,
                "step_retry_count": retry_count + 1,
                "needs_replanning": False,
            }
        else:
            # Retry same agent
            logger.info(
                "Step %s failed, retrying with %s (retry %d/%d)",
                last_result.get("step_id", "?"),
                current_agent,
                retry_count + 1,
                max_retries,
            )
            return {
                "step_retry_count": retry_count + 1,
                "needs_replanning": False,
            }

    # Exceeded retries → trigger replanning
    logger.warning(
        "Step %s failed after %d retries, triggering replan",
        last_result.get("step_id", "?"),
        max_retries,
    )
    return {
        "needs_replanning": True,
        "step_retry_count": 0,
    }


def _evaluate_approved_plan_step(
    state: dict[str, Any],
    plan: list[dict[str, Any]],
    current_step: int,
    step_results: list[dict[str, Any]],
    max_retries: int,
    retry_count: int,
) -> dict[str, Any]:
    if current_step >= len(plan):
        failed = [r for r in step_results if r.get("status") not in ("success", "skipped")]
        if not failed:
            return {"done": True, "step_retry_count": 0}
        first_fail = failed[0]
        fail_idx = next((i for i, s in enumerate(plan) if s.get("step_id") == first_fail.get("step_id")), None)
        if fail_idx is not None and retry_count < max_retries:
            return _handle_approved_failure(state, fail_idx, first_fail, retry_count + 1)
        return _emit_replan_request(state, first_fail)

    last_result = step_results[-1]
    status = last_result.get("status", "error")
    if status in {"success", "skipped"}:
        next_step = current_step + 1
        if next_step >= len(plan):
            return {"current_step": next_step, "done": True, "step_retry_count": 0}
        return {"current_step": next_step, "step_retry_count": 0, "needs_replanning": False}

    if retry_count < max_retries:
        return _handle_approved_failure(state, current_step, last_result, retry_count + 1)
    return _emit_replan_request(state, last_result)


def _handle_approved_failure(
    state: dict[str, Any],
    step_index: int,
    failed_result: dict[str, Any],
    next_retry_count: int,
) -> dict[str, Any]:
    plan = [dict(step) for step in state.get("plan", [])]
    step = dict(plan[step_index])
    fallback = dict(step.get("fallback_strategy", {}) or {})
    fallback_action = str(fallback.get("action", "replan"))
    fallback_tool_id = fallback.get("fallback_tool_id")

    if fallback_action == "use_alternative_tool" and fallback_tool_id:
        logger.info(
            "Approved plan step %s failed; switching to fallback tool %s",
            failed_result.get("step_id", "?"),
            fallback_tool_id,
        )
        step["tool_id"] = fallback_tool_id
        step["description"] = f"{step.get('description', '')} [fallback -> {fallback_tool_id}]".strip()
        plan[step_index] = step
        clean_results = [r for r in state.get("step_results", []) if r.get("step_id") != failed_result.get("step_id")]
        return {
            "plan": plan,
            "current_step": step_index,
            "step_results": clean_results,
            "step_retry_count": next_retry_count,
            "needs_replanning": False,
        }

    if fallback_action == "retry":
        logger.info(
            "Approved plan step %s failed; retrying (%d)",
            failed_result.get("step_id", "?"),
            next_retry_count,
        )
        return {"step_retry_count": next_retry_count, "needs_replanning": False}

    return _emit_replan_request(state, failed_result)


def _emit_replan_request(state: dict[str, Any], failed_result: dict[str, Any]) -> dict[str, Any]:
    approved_plan = state.get("approved_plan", {})
    request = {
        "plan_id": approved_plan.get("plan_id", ""),
        "revision": approved_plan.get("revision", 1),
        "reason": "execution_failure",
        "failed_step_id": failed_result.get("step_id", ""),
        "tool_id": failed_result.get("tool_id", ""),
        "error": failed_result.get("error", ""),
        "error_details": failed_result.get("error_details"),
    }
    logger.warning(
        "Approved plan %s requires replan after step %s",
        request["plan_id"],
        request["failed_step_id"],
    )
    return {"done": True, "step_retry_count": 0, "needs_replanning": False, "replan_request": request}


def _pick_alternative_agent(
    current: str, available: list[str]
) -> str | None:
    """Pick an alternative agent from the available pool."""
    alternatives = [a for a in available if a != current]
    return alternatives[0] if alternatives else None


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final report from all step results."""
    if state.get("approved_plan"):
        return _finalize_approved_plan(state)

    step_results = state.get("step_results", [])
    plan = state.get("plan", [])
    error = state.get("error")

    if error:
        return {"final_report": f"Error: {error}", "done": True}

    # Preserve existing report (e.g. from dry-run)
    existing_report = state.get("final_report", "")
    if existing_report and not step_results:
        return {"final_report": existing_report, "done": True}

    if not step_results:
        return {"final_report": "No steps were executed.", "done": True}

    lines: list[str] = ["=== Dispatch Report ===", ""]

    success_count = sum(1 for r in step_results if r.get("status") == "success")
    error_count = sum(1 for r in step_results if r.get("status") == "error")
    skipped_count = sum(1 for r in step_results if r.get("status") == "skipped")
    total = len(step_results)

    lines.append(
        f"Results: {success_count} succeeded, {error_count} failed, "
        f"{skipped_count} skipped out of {total} executions"
    )
    lines.append("")

    for r in step_results:
        status_icon = {"success": "✅", "error": "❌", "timeout": "⏰", "skipped": "⏭️"}.get(
            r.get("status", ""), "❓"
        )
        step_desc = ""
        for s in plan:
            if s.get("step_id") == r.get("step_id"):
                step_desc = s.get("description", "")
                break

        lines.append(
            f"{status_icon} {r.get('step_id', '?')} [{r.get('agent', '?')}]: "
            f"{step_desc or r.get('status', '?')}"
        )

        if r.get("status") == "error" and r.get("error"):
            lines.append(f"   Error: {r['error'][:200]}")

        if r.get("output"):
            # Show a brief extract of successful output
            output_preview = r["output"].strip()[:300]
            if output_preview:
                lines.append(f"   Output: {output_preview}")

        lines.append("")

    # Cleanup context directory unless keep_context is set
    _cleanup_context_dir(state)

    return {"final_report": "\n".join(lines), "done": True}


def _finalize_approved_plan(state: dict[str, Any]) -> dict[str, Any]:
    step_results = state.get("step_results", [])
    approved_plan = state.get("approved_plan", {})
    error = state.get("error")
    if error:
        return {"final_report": f"Error: {error}", "done": True}

    existing_report = state.get("final_report", "")
    if existing_report and not step_results:
        return {"final_report": existing_report, "done": True}

    lines = [
        "=== Approved Plan Execution ===",
        f"Plan: {approved_plan.get('plan_id', '?')} (rev {approved_plan.get('revision', '?')})",
        f"Goal: {approved_plan.get('user_goal', '')}",
        "",
    ]
    success_count = sum(1 for r in step_results if r.get("status") == "success")
    error_count = sum(1 for r in step_results if r.get("status") == "error")
    skipped_count = sum(1 for r in step_results if r.get("status") == "skipped")
    total = len(step_results)
    lines.append(
        f"Results: {success_count} succeeded, {error_count} failed, {skipped_count} skipped out of {total} executions"
    )
    lines.append("")

    for result in step_results:
        status_icon = {"success": "✅", "error": "❌", "timeout": "⏰", "skipped": "⏭️"}.get(
            result.get("status", ""), "❓"
        )
        tool_id = result.get("tool_id", "")
        lines.append(
            f"{status_icon} {result.get('step_id', '?')} [{tool_id or result.get('agent', '?')}]: {result.get('status', '?')}"
        )
        if result.get("error"):
            lines.append(f"   Error: {str(result['error'])[:200]}")
        output = result.get("output")
        if output:
            output_preview = output if isinstance(output, str) else str(output)
            output_preview = output_preview.strip()[:300]
            if output_preview:
                lines.append(f"   Output: {output_preview}")
        lines.append("")

    if state.get("replan_request"):
        lines.append("Replan Required:")
        lines.append(str(state["replan_request"]))
        lines.append("")

    _cleanup_context_dir(state)
    return {"final_report": "\n".join(lines), "done": True}


def _cleanup_context_dir(state: dict[str, Any]) -> None:
    """Remove the session context directory if it exists and cleanup is not disabled."""
    if state.get("keep_context"):
        return
    context_dir = state.get("context_dir")
    if not context_dir:
        return
    path = Path(context_dir)
    if path.exists() and path.is_dir():
        try:
            shutil.rmtree(path)
            logger.info("Cleaned up context directory: %s", path)
        except Exception as e:
            logger.warning("Failed to clean up context directory %s: %s", path, e)
