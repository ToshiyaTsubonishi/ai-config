"""Tests for workflow loading and rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_config.dispatch.workflow import (
    _parse_workflow_file,
    _validate_step,
    list_workflows,
    load_workflow,
    render_workflow_steps,
)


@pytest.fixture
def workflow_dir(tmp_path: Path) -> Path:
    """Create a temp directory with sample workflows."""
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()

    (wf_dir / "test-workflow.yaml").write_text(
        """
name: test-workflow
description: A test workflow
variables:
  lang: Python
steps:
  - step_id: step-1
    description: First step
    agent: gemini
    prompt_template: "Do {user_prompt} in {lang}"
    timeout_seconds: 60
  - step_id: step-2
    description: Second step
    agent: codex
    depends_on: [step-1]
    prompt_template: "Verify {user_prompt}"
    timeout_seconds: 120
""",
        encoding="utf-8",
    )

    (wf_dir / "parallel-workflow.yaml").write_text(
        """
name: parallel-workflow
description: Steps without dependencies (parallelizable)
steps:
  - step_id: a
    description: Task A
    agent: gemini
    prompt_template: "Do A for {user_prompt}"
  - step_id: b
    description: Task B
    agent: codex
    prompt_template: "Do B for {user_prompt}"
""",
        encoding="utf-8",
    )

    return wf_dir


class TestValidateStep:
    def test_defaults(self):
        result = _validate_step({}, 0)
        assert result["step_id"] == "step-1"
        assert result["agent"] == "gemini"
        assert result["timeout_seconds"] == 300

    def test_preserves_values(self):
        result = _validate_step(
            {"step_id": "custom", "agent": "codex", "timeout_seconds": 60}, 0
        )
        assert result["step_id"] == "custom"
        assert result["agent"] == "codex"


class TestLoadWorkflow:
    def test_loads_yaml(self, workflow_dir):
        wf = load_workflow("test-workflow", workflow_dir)
        assert wf is not None
        assert wf["name"] == "test-workflow"
        assert len(wf["steps"]) == 2

    def test_not_found(self, tmp_path):
        assert load_workflow("nonexistent", tmp_path) is None


class TestRenderWorkflowSteps:
    def test_renders_templates(self, workflow_dir):
        wf = load_workflow("test-workflow", workflow_dir)
        steps = render_workflow_steps(wf, "build app")
        assert "build app" in steps[0]["prompt"]
        assert "Python" in steps[0]["prompt"]  # from variables
        assert steps[1]["depends_on"] == ["step-1"]

    def test_custom_variables(self, workflow_dir):
        wf = load_workflow("test-workflow", workflow_dir)
        steps = render_workflow_steps(wf, "test", variables={"lang": "Go"})
        assert "Go" in steps[0]["prompt"]


class TestListWorkflows:
    def test_lists(self, workflow_dir):
        results = list_workflows(workflow_dir)
        names = [r["name"] for r in results]
        assert "test-workflow" in names
        assert "parallel-workflow" in names


class TestParallelDispatchHelpers:
    """Test the parallel batch detection in dispatcher."""

    def test_find_parallel_batch(self):
        from ai_config.dispatch.dispatcher import _find_parallel_batch

        plan = [
            {"step_id": "a", "depends_on": []},
            {"step_id": "b", "depends_on": []},
            {"step_id": "c", "depends_on": ["a", "b"]},
        ]
        # Steps a and b have no deps → parallelizable
        batch = _find_parallel_batch(plan, 0, set())
        assert batch == [0, 1]

    def test_no_parallel_single_step(self):
        from ai_config.dispatch.dispatcher import _find_parallel_batch

        plan = [
            {"step_id": "a", "depends_on": []},
            {"step_id": "b", "depends_on": ["a"]},
        ]
        # Only step a is eligible, but single step → empty batch
        batch = _find_parallel_batch(plan, 0, set())
        assert batch == []

    def test_deps_met(self):
        from ai_config.dispatch.dispatcher import _find_parallel_batch

        plan = [
            {"step_id": "a", "depends_on": []},
            {"step_id": "b", "depends_on": ["a"]},
            {"step_id": "c", "depends_on": ["a"]},
        ]
        # a is done, b and c both depend on a → parallelizable
        batch = _find_parallel_batch(plan, 1, {"a"})
        assert batch == [1, 2]

    def test_find_parallel_batch_non_contiguous(self):
        """Steps with no deps should be collected even when separated by unmet-dep steps."""
        from ai_config.dispatch.dispatcher import _find_parallel_batch

        plan = [
            {"step_id": "a", "depends_on": []},
            {"step_id": "b", "depends_on": ["x"]},  # x not completed
            {"step_id": "c", "depends_on": []},
        ]
        # a and c are parallelizable; b is skipped (dep "x" unmet)
        batch = _find_parallel_batch(plan, 0, set())
        assert batch == [0, 2]


class TestContextHandoff:
    """Test context directory management."""

    def test_save_and_load_context(self, tmp_path):
        from ai_config.dispatch.dispatcher import (
            _load_context_for_step,
            _save_step_context,
        )

        ctx_dir = tmp_path / "context"
        ctx_dir.mkdir()

        _save_step_context(
            ctx_dir,
            "step-1",
            {"agent": "gemini", "status": "success", "output": "Hello from step 1"},
        )

        context = _load_context_for_step(ctx_dir, ["step-1"])
        assert "Hello from step 1" in context
        assert "step-1" in context

    def test_missing_deps_returns_empty(self, tmp_path):
        from ai_config.dispatch.dispatcher import _load_context_for_step

        ctx_dir = tmp_path / "context"
        ctx_dir.mkdir()

        context = _load_context_for_step(ctx_dir, ["nonexistent"])
        assert context == ""

    def test_no_deps_returns_empty(self, tmp_path):
        from ai_config.dispatch.dispatcher import _load_context_for_step

        ctx_dir = tmp_path / "context"
        ctx_dir.mkdir()

        context = _load_context_for_step(ctx_dir, [])
        assert context == ""
