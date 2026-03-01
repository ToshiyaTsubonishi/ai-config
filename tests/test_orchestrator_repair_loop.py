from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from ai_config.orchestrator.graph import create_agent
from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def _build_adapter_index(index_dir: Path) -> None:
    records = [
        ToolRecord(
            id="toolchain:codex",
            name="codex",
            description="codex execution adapter",
            source_path="src/ai_config/executor/adapters/codex.py",
            tool_kind="toolchain_adapter",
            metadata={"enabled_targets": ["codex"]},
            invoke={"backend": "cli", "command": "codex", "args": [], "timeout_ms": 10000, "env_keys": []},
            tags=["target:codex", "capability:cli_execution"],
        ),
        ToolRecord(
            id="toolchain:gemini_cli",
            name="gemini_cli",
            description="gemini execution adapter",
            source_path="src/ai_config/executor/adapters/gemini_cli.py",
            tool_kind="toolchain_adapter",
            metadata={"enabled_targets": ["gemini_cli"]},
            invoke={"backend": "cli", "command": "gemini", "args": [], "timeout_ms": 10000, "env_keys": []},
            tags=["target:gemini_cli", "capability:cli_execution"],
        ),
    ]
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")


def _base_state(query: str) -> dict[str, object]:
    return {
        "query": query,
        "top_k": 8,
        "max_retries": 2,
        "trace": False,
        "retrieval_attempts": 0,
        "candidates": [],
        "execution_results": [],
        "recovery_path": [],
        "adopted_tools": [],
        "unmet": [],
        "error": None,
        "final_answer": "",
    }


def test_step_failure_then_repair_alternative(monkeypatch, tmp_path: Path) -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx is required for this test environment")

    index_dir = tmp_path / "index"
    _build_adapter_index(index_dir)

    monkeypatch.setenv("AI_CONFIG_CODEX_CMD", "missing-codex-cli")
    monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "npx")

    agent = create_agent(index_dir=index_dir, repo_root=tmp_path)
    result = agent.invoke(_base_state("codex gemini run"))

    results = result.get("execution_results", [])
    assert any(r.get("status") == "error" for r in results)
    assert any(r.get("status") == "success" and r.get("tool_id") == "toolchain:gemini_cli" for r in results)
    assert any("repair_alternative" in step for step in result.get("recovery_path", []))


def test_repair_fail_then_reretrieve_success(monkeypatch, tmp_path: Path) -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx is required for this test environment")

    index_dir = tmp_path / "index"
    _build_adapter_index(index_dir)

    monkeypatch.setenv("AI_CONFIG_CODEX_CMD", "missing-codex-cli")
    monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "npx")

    agent = create_agent(index_dir=index_dir, repo_root=tmp_path)
    result = agent.invoke(_base_state("codex run please"))

    assert any("re_retrieve" in step for step in result.get("recovery_path", []))
    assert any(
        r.get("status") == "success" and r.get("tool_id") == "toolchain:gemini_cli"
        for r in result.get("execution_results", [])
    )

