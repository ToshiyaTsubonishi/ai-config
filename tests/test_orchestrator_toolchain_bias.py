from __future__ import annotations

from pathlib import Path

from ai_config.orchestrator.planner import OrchestrationPlanner
from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def test_fallback_plan_prefers_toolchain_for_action_oriented_software_query(monkeypatch, tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    records = [
        ToolRecord(
            id="skill:generic-fix-guide",
            name="generic-fix-guide",
            description="Fix bug test build review refactor guide for general development tasks",
            source_path="skills/shared/generic/SKILL.md",
            tool_kind="skill",
            metadata={"enabled_targets": [], "executable": True},
        ),
        ToolRecord(
            id="toolchain:codex",
            name="codex",
            description="Codex adapter",
            source_path="src/ai_config/executor/adapters/codex.py",
            tool_kind="toolchain_adapter",
            metadata={"enabled_targets": ["codex"], "domain": "toolchain", "executable": True},
            tags=["target:codex", "capability:cli_execution"],
            invoke={"backend": "cli", "command": "codex", "args": [], "timeout_ms": 1000, "env_keys": []},
        ),
    ]
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")

    planner = OrchestrationPlanner(index_dir=index_dir, repo_root=tmp_path)
    monkeypatch.setattr(planner, "_get_llm", lambda: None)

    result = planner.create_plan("fix the bug and run the test build review", top_k=3)

    assert result.plan.steps
    assert result.plan.steps[0].tool_ref.tool_id == "toolchain:codex"
