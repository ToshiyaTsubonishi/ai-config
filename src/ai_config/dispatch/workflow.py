"""Workflow definitions – reusable dispatch plans loadable from YAML.

Workflows allow defining common multi-agent patterns that can be
invoked from any CLI tool (Antigravity, Gemini CLI, Codex).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default workflow directory
# ---------------------------------------------------------------------------
DEFAULT_WORKFLOW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "workflows"


# ---------------------------------------------------------------------------
# Workflow schema
# ---------------------------------------------------------------------------
def _validate_step(step: dict[str, Any], idx: int) -> dict[str, Any]:
    """Validate and normalize a workflow step definition."""
    step_id = step.get("step_id", f"step-{idx + 1}")
    return {
        "step_id": step_id,
        "description": step.get("description", ""),
        "agent": step.get("agent", "gemini"),
        "prompt_template": step.get("prompt_template", step.get("prompt", "")),
        "depends_on": step.get("depends_on", []),
        "working_directory": step.get("working_directory", "."),
        "timeout_seconds": step.get("timeout_seconds", 300),
    }


def load_workflow(
    name: str,
    workflow_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Load a workflow definition by name.

    Searches for <name>.yaml or <name>.yml in the workflow directory.
    Returns the parsed workflow dict or None if not found.
    """
    search_dirs = [
        workflow_dir or DEFAULT_WORKFLOW_DIR,
        Path.cwd() / ".agents" / "workflows",
        Path.cwd() / "workflows",
    ]

    for d in search_dirs:
        for ext in (".yaml", ".yml"):
            path = d / f"{name}{ext}"
            if path.exists():
                logger.info("Loading workflow: %s", path)
                return _parse_workflow_file(path)

    logger.warning("Workflow '%s' not found in %s", name, search_dirs)
    return None


def _parse_workflow_file(path: Path) -> dict[str, Any]:
    """Parse a workflow YAML file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Workflow file must be a YAML mapping: {path}")

    steps = raw.get("steps", [])
    validated_steps = [_validate_step(s, i) for i, s in enumerate(steps)]

    return {
        "name": raw.get("name", path.stem),
        "description": raw.get("description", ""),
        "steps": validated_steps,
        "variables": raw.get("variables", {}),
    }


def render_workflow_steps(
    workflow: dict[str, Any],
    user_prompt: str,
    variables: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Render workflow step templates with user prompt and variables.

    Template variables supported:
    - {user_prompt} — the original user request
    - {working_directory} — current working directory
    - Any key from workflow.variables or the variables parameter
    """
    merged_vars = {
        "user_prompt": user_prompt,
        **(workflow.get("variables", {})),
        **(variables or {}),
    }

    rendered: list[dict[str, Any]] = []
    for step in workflow["steps"]:
        prompt = step.get("prompt_template", "")
        try:
            prompt = prompt.format(**merged_vars)
        except KeyError:
            # Leave unresolved placeholders as-is
            pass

        rendered.append({
            "step_id": step["step_id"],
            "description": step.get("description", ""),
            "agent": step["agent"],
            "prompt": prompt,
            "depends_on": step.get("depends_on", []),
            "working_directory": step.get("working_directory", "."),
            "timeout_seconds": step.get("timeout_seconds", 300),
        })

    return rendered


def list_workflows(
    workflow_dir: Path | None = None,
) -> list[dict[str, str]]:
    """List all available workflow definitions."""
    results: list[dict[str, str]] = []
    search_dirs = [
        workflow_dir or DEFAULT_WORKFLOW_DIR,
        Path.cwd() / ".agents" / "workflows",
        Path.cwd() / "workflows",
    ]
    seen: set[str] = set()

    for d in search_dirs:
        if not d.exists():
            continue
        for path in sorted([*d.glob("*.yaml"), *d.glob("*.yml")]):
            name = path.stem
            if name in seen:
                continue
            seen.add(name)
            try:
                wf = _parse_workflow_file(path)
                results.append({
                    "name": name,
                    "description": wf.get("description", ""),
                    "path": str(path),
                    "steps": str(len(wf.get("steps", []))),
                })
            except Exception as e:
                logger.warning("Failed to parse workflow %s: %s", path, e)

    return results
