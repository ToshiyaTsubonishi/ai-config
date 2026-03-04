"""Tests for code review fixes: env filter, CLI command builder, dep skip, cleanup."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai_config.dispatch.dispatcher import (
    _build_cli_command,
    _build_safe_env,
    _SAFE_ENV_KEYS,
)
from ai_config.dispatch.evaluator import _cleanup_context_dir, finalize


class TestSafeEnvFilter:
    """Verify that environment variable filtering works correctly."""

    def test_filters_unsafe_keys(self, monkeypatch):
        monkeypatch.setenv("PATH", "/usr/bin")
        monkeypatch.setenv("SECRET_TOKEN", "should-not-appear")
        monkeypatch.setenv("DATABASE_URL", "postgres://secret")
        env = _build_safe_env()
        assert "PATH" in env
        assert "SECRET_TOKEN" not in env
        assert "DATABASE_URL" not in env

    def test_includes_agent_env_vars(self, monkeypatch):
        monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "/usr/local/bin/gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        env = _build_safe_env()
        assert env["AI_CONFIG_GEMINI_CMD"] == "/usr/local/bin/gemini"
        assert env["GEMINI_API_KEY"] == "test-key"

    def test_missing_keys_not_included(self):
        env = _build_safe_env()
        # Keys not in os.environ should not appear
        for key in env:
            assert key in os.environ


class TestBuildCliCommand:
    """Test CLI command construction for each agent type."""

    def test_gemini_command(self, monkeypatch):
        monkeypatch.delenv("AI_CONFIG_GEMINI_CMD", raising=False)
        cmd = _build_cli_command("gemini", "hello world")
        assert cmd == ["gemini", "-p", "hello world", "--yolo"]

    def test_codex_command(self, monkeypatch):
        monkeypatch.delenv("AI_CONFIG_CODEX_CMD", raising=False)
        cmd = _build_cli_command("codex", "fix bug")
        assert cmd == ["codex", "exec", "fix bug", "--full-auto"]

    def test_antigravity_command(self, monkeypatch):
        monkeypatch.delenv("AI_CONFIG_ANTIGRAVITY_CMD", raising=False)
        cmd = _build_cli_command("antigravity", "check UI")
        assert cmd == ["antigravity", "--prompt", "check UI"]

    def test_custom_command_via_env(self, monkeypatch):
        monkeypatch.setenv("AI_CONFIG_GEMINI_CMD", "/custom/gemini")
        cmd = _build_cli_command("gemini", "test")
        assert cmd[0] == "/custom/gemini"

    def test_unknown_agent_fallback(self):
        cmd = _build_cli_command("unknown_agent", "do stuff")
        assert cmd == ["unknown_agent", "do stuff"]


class TestDependencySkip:
    """Test that steps with unmet dependencies are skipped."""

    def test_unmet_deps_skipped(self, monkeypatch):
        from ai_config.dispatch.dispatcher import dispatch_step

        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        state = {
            "plan": [
                {"step_id": "s1", "depends_on": [], "agent": "gemini", "prompt": "a"},
                {"step_id": "s2", "depends_on": ["s1"], "agent": "gemini", "prompt": "b"},
            ],
            "current_step": 1,
            "step_results": [
                {"step_id": "s1", "status": "error", "agent": "gemini"},
            ],
            "working_directory": "/tmp",
            "parallel": False,
        }
        result = dispatch_step(state)
        # s2 should be skipped because s1 failed (not in completed_ids)
        last = result["step_results"][-1]
        assert last["status"] == "skipped"
        assert "s1" in last["error"]


class TestContextCleanup:
    """Test .dispatch/ context directory cleanup."""

    def test_cleanup_removes_dir(self, tmp_path):
        ctx_dir = tmp_path / "session123"
        ctx_dir.mkdir()
        (ctx_dir / "step-1.json").write_text("{}")
        state = {"context_dir": str(ctx_dir)}
        _cleanup_context_dir(state)
        assert not ctx_dir.exists()

    def test_keep_context_preserves_dir(self, tmp_path):
        ctx_dir = tmp_path / "session456"
        ctx_dir.mkdir()
        (ctx_dir / "step-1.json").write_text("{}")
        state = {"context_dir": str(ctx_dir), "keep_context": True}
        _cleanup_context_dir(state)
        assert ctx_dir.exists()

    def test_no_context_dir_is_noop(self):
        state = {}
        _cleanup_context_dir(state)  # should not raise

    def test_finalize_calls_cleanup(self, tmp_path):
        ctx_dir = tmp_path / "session789"
        ctx_dir.mkdir()
        (ctx_dir / "step-1.json").write_text("{}")
        state = {
            "plan": [{"step_id": "s1", "description": "test"}],
            "step_results": [
                {"step_id": "s1", "agent": "gemini", "status": "success", "output": "ok", "error": ""},
            ],
            "context_dir": str(ctx_dir),
        }
        result = finalize(state)
        assert result["done"] is True
        assert not ctx_dir.exists()


class TestReplanResetsResults:
    """Verify that replan_tasks resets step_results."""

    def test_step_results_reset_on_replan(self, monkeypatch):
        from ai_config.dispatch.planner import replan_tasks, _get_llm

        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        # Clear lru_cache before patching
        _get_llm.cache_clear()
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: None
        )
        state = {
            "user_prompt": "test",
            "replan_count": 0,
            "max_replans": 2,
            "available_agents": ["gemini"],
            "working_directory": ".",
            "step_results": [
                {"step_id": "step-1", "agent": "gemini", "status": "error", "error": "failed"},
                {"step_id": "step-2", "agent": "gemini", "status": "success", "output": "ok"},
            ],
        }
        result = replan_tasks(state)
        assert result["step_results"] == []
        assert result["replan_count"] == 1
