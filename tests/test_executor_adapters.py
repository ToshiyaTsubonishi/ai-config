from __future__ import annotations

import platform
import sys
from pathlib import Path

import pytest

from ai_config.executor.mcp_wrapper import ToolExecutor
from ai_config.registry.models import ToolRecord

IS_WINDOWS = platform.system() == "Windows"


@pytest.mark.skipif(not IS_WINDOWS, reason="cmd.exe only available on Windows")
def test_adapter_success_and_missing_cli(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_CONFIG_CODEX_CMD", "cmd")
    executor = ToolExecutor(repo_root=tmp_path)
    ok = executor.tools_call("toolchain:codex", "run", {"args": ["/c", "echo", "ok"]})
    assert ok["status"] == "success"

    monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "missing-cli-command-xyz")
    executor2 = ToolExecutor(repo_root=tmp_path)
    missing = executor2.tools_call("toolchain:gemini_cli", "run", {"args": ["--help"]})
    assert missing["status"] == "error"
    assert missing["error"]["code"] == "EXECUTOR_NOT_AVAILABLE"


def test_adapter_missing_cli_cross_platform(monkeypatch, tmp_path: Path) -> None:
    """Missing CLI returns EXECUTOR_NOT_AVAILABLE on any platform."""
    monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "missing-cli-command-xyz")
    executor = ToolExecutor(repo_root=tmp_path)
    missing = executor.tools_call("toolchain:gemini_cli", "run", {"args": ["--help"]})
    assert missing["status"] == "error"
    assert missing["error"]["code"] == "EXECUTOR_NOT_AVAILABLE"


def test_allowlist_errors(tmp_path: Path) -> None:
    """Non-allowlisted commands are denied."""
    executor = ToolExecutor(repo_root=tmp_path)
    bad_record = ToolRecord(
        id="mcp:bad",
        name="bad",
        description="bad command",
        source_path="config/master/ai-sync.yaml",
        tool_kind="mcp_server",
        invoke={"command": "forbidden_cmd", "args": [], "timeout_ms": 1000, "env_keys": []},
    )
    executor.register_records([bad_record])
    denied = executor.tools_call("mcp:bad", "run", {})
    assert denied["status"] == "error"
    assert denied["error"]["code"] == "EXECUTOR_NOT_ALLOWED"


@pytest.mark.skipif(not IS_WINDOWS, reason="timeout /t only available on Windows")
def test_timeout_errors_windows(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_CONFIG_CODEX_CMD", "cmd")
    executor = ToolExecutor(repo_root=tmp_path)
    timeout = executor.tools_call(
        "toolchain:codex",
        "run",
        {"args": ["/c", "timeout", "/t", "2", "/nobreak"], "timeout_ms": 100},
    )
    assert timeout["status"] == "error"
    assert timeout["error"]["code"] == "EXECUTOR_TIMEOUT"
