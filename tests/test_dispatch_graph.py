"""Tests for the dispatch graph wiring and integration."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("langgraph")

from ai_config.dispatch.evaluator import evaluate_step, finalize
from ai_config.dispatch.graph import build_dispatch_graph, create_dispatch_agent


class TestEvaluateStep:
    def test_success_advances_to_next(self):
        state = {
            "plan": [{"step_id": "s1"}, {"step_id": "s2"}],
            "current_step": 0,
            "step_results": [{"step_id": "s1", "status": "success", "agent": "gemini"}],
            "max_retries": 2,
            "step_retry_count": 0,
            "available_agents": ["gemini"],
        }
        result = evaluate_step(state)
        assert result["current_step"] == 1
        assert result.get("done") is not True

    def test_success_last_step_finalizes(self):
        state = {
            "plan": [{"step_id": "s1"}],
            "current_step": 0,
            "step_results": [{"step_id": "s1", "status": "success", "agent": "gemini"}],
            "max_retries": 2,
            "step_retry_count": 0,
            "available_agents": ["gemini"],
        }
        result = evaluate_step(state)
        assert result["done"] is True

    def test_failure_retries_with_alt_agent(self):
        state = {
            "plan": [{"step_id": "s1", "agent": "codex"}],
            "current_step": 0,
            "step_results": [{"step_id": "s1", "status": "error", "agent": "codex", "error": "fail"}],
            "max_retries": 2,
            "step_retry_count": 0,
            "available_agents": ["codex", "gemini"],
        }
        result = evaluate_step(state)
        assert result["step_retry_count"] == 1
        # Should switch to alternative agent
        if "plan" in result:
            assert result["plan"][0]["agent"] == "gemini"

    def test_failure_triggers_replan_after_max_retries(self):
        state = {
            "plan": [{"step_id": "s1", "agent": "codex"}],
            "current_step": 0,
            "step_results": [{"step_id": "s1", "status": "error", "agent": "codex", "error": "fail"}],
            "max_retries": 2,
            "step_retry_count": 2,
            "available_agents": ["codex"],
        }
        result = evaluate_step(state)
        assert result["needs_replanning"] is True


class TestFinalize:
    def test_generates_report(self):
        state = {
            "plan": [
                {"step_id": "s1", "description": "Design"},
                {"step_id": "s2", "description": "Implement"},
            ],
            "step_results": [
                {"step_id": "s1", "agent": "gemini", "status": "success", "output": "done", "error": ""},
                {"step_id": "s2", "agent": "codex", "status": "error", "output": "", "error": "compile error"},
            ],
        }
        result = finalize(state)
        assert "Dispatch Report" in result["final_report"]
        assert "✅" in result["final_report"]
        assert "❌" in result["final_report"]
        assert result["done"] is True

    def test_error_state(self):
        state = {"error": "Something broke", "step_results": [], "plan": []}
        result = finalize(state)
        assert "Error" in result["final_report"]

    def test_empty_results(self):
        state = {"step_results": [], "plan": []}
        result = finalize(state)
        assert "No steps" in result["final_report"]


class TestGraphWiring:
    def test_graph_compiles(self):
        graph = build_dispatch_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_dry_run_end_to_end(self, monkeypatch):
        """Dry-run should produce a plan report without dispatching."""
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: None
        )
        agent = create_dispatch_agent()
        result = agent.invoke(
            {
                "user_prompt": "Create a hello world app",
                "working_directory": ".",
                "dry_run": True,
                "max_retries": 1,
                "max_replans": 1,
                "step_results": [],
                "replan_count": 0,
                "done": False,
                "abort": False,
                "needs_replanning": False,
                "error": None,
                "final_report": "",
            }
        )
        assert result.get("done") is True
        assert "dry-run" in result.get("final_report", "")

    def test_dispatch_with_mock_agent(self, monkeypatch):
        """Full dispatch with mocked subprocess should succeed."""
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: None
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Task completed successfully"
        mock_result.stderr = ""

        monkeypatch.setattr(
            "ai_config.dispatch.dispatcher.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        agent = create_dispatch_agent()
        result = agent.invoke(
            {
                "user_prompt": "Say hello",
                "working_directory": ".",
                "dry_run": False,
                "max_retries": 1,
                "max_replans": 1,
                "step_results": [],
                "replan_count": 0,
                "done": False,
                "abort": False,
                "needs_replanning": False,
                "error": None,
                "final_report": "",
            }
        )
        assert result.get("done") is True
        report = result.get("final_report", "")
        assert "Dispatch Report" in report
        assert "✅" in report
