"""Evaluator – assesses step results and decides next action."""

from __future__ import annotations

import logging
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

    if not step_results:
        return {"done": True, "error": "No step results to evaluate"}

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


def _pick_alternative_agent(
    current: str, available: list[str]
) -> str | None:
    """Pick an alternative agent from the available pool."""
    alternatives = [a for a in available if a != current]
    return alternatives[0] if alternatives else None


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final report from all step results."""
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

    return {"final_report": "\n".join(lines), "done": True}
