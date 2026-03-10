from __future__ import annotations

from pathlib import Path

import pytest

from ai_config.executor.command_resolution import resolve_command_spec
from ai_config.executor.errors import ExecutorErrorCode


def test_resolve_command_spec_expands_workspace_root_and_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PROJECT_ID", "demo-project")

    resolved = resolve_command_spec(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "${WORKSPACE_ROOT}", "{{PROJECT_ID}}"],
        repo_root=tmp_path,
        env_keys=["PROJECT_ID"],
        cwd=".",
    )

    assert resolved.args[2] == str(tmp_path.resolve())
    assert resolved.args[3] == "demo-project"
    assert resolved.cwd == tmp_path.resolve()
    assert resolved.env["PROJECT_ID"] == "demo-project"


def test_resolve_command_spec_missing_placeholder_fails(tmp_path: Path) -> None:
    with pytest.raises(Exception) as exc_info:
        resolve_command_spec(
            command="npx",
            args=["-y", "mcp-remote", "{{MISSING_TOKEN}}"],
            repo_root=tmp_path,
            env_keys=["MISSING_TOKEN"],
            cwd=".",
        )

    error = exc_info.value
    assert getattr(error, "code", None) == ExecutorErrorCode.EXECUTOR_CONFIG_ERROR
