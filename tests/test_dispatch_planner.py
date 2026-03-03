"""Tests for dispatch planner module."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai_config.dispatch.planner import (
    AGENT_PROFILES,
    _fallback_single_step,
    _parse_plan_json,
    detect_available_agents,
    plan_tasks,
    replan_tasks,
)


class TestDetectAvailableAgents:
    def test_detects_available(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/gemini" if cmd == "gemini" else None)
        result = detect_available_agents()
        assert "gemini" in result
        assert "codex" not in result

    def test_preferred_filter(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        result = detect_available_agents(preferred=["codex"])
        assert result == ["codex"]

    def test_preferred_fallback_if_unavailable(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/gemini" if cmd == "gemini" else None)
        result = detect_available_agents(preferred=["codex"])
        assert "gemini" in result

    def test_no_agents_available(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: None)
        result = detect_available_agents()
        assert result == []


class TestParsePlanJson:
    def test_plain_json(self):
        raw = '{"steps": [{"step_id": "step-1"}], "summary": "test"}'
        data = _parse_plan_json(raw)
        assert data["steps"][0]["step_id"] == "step-1"

    def test_fenced_json(self):
        raw = '```json\n{"steps": [], "summary": "test"}\n```'
        data = _parse_plan_json(raw)
        assert data["steps"] == []

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_plan_json("not json at all")


class TestFallbackPlan:
    def test_creates_single_step(self):
        plan = _fallback_single_step("do something", ["gemini"], "/work")
        assert len(plan["steps"]) == 1
        assert plan["steps"][0]["agent"] == "gemini"
        assert plan["steps"][0]["prompt"] == "do something"
        assert plan["steps"][0]["working_directory"] == "/work"


class TestPlanTasks:
    def test_no_agents_returns_error(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: None)
        state = {"user_prompt": "test", "working_directory": "."}
        result = plan_tasks(state)
        assert result["done"] is True
        assert "No CLI agents" in result.get("error", "")

    def test_llm_failure_uses_fallback(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: None
        )
        state = {"user_prompt": "build a thing", "working_directory": "."}
        result = plan_tasks(state)
        assert len(result["plan"]) == 1
        assert result["plan"][0]["agent"] in AGENT_PROFILES

    def test_dry_run_produces_report(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: None
        )
        state = {"user_prompt": "test task", "working_directory": ".", "dry_run": True}
        result = plan_tasks(state)
        assert result["done"] is True
        assert "dry-run" in result["final_report"]

    def test_validates_agent_assignments(self, monkeypatch):
        monkeypatch.setattr(
            "shutil.which",
            lambda cmd: "/usr/bin/gemini" if cmd == "gemini" else None,
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps(
                {
                    "steps": [
                        {
                            "step_id": "step-1",
                            "description": "test",
                            "agent": "invalid_agent",
                            "prompt": "do it",
                            "depends_on": [],
                            "working_directory": ".",
                            "timeout_seconds": 60,
                        }
                    ],
                    "summary": "test plan",
                }
            )
        )
        monkeypatch.setattr(
            "ai_config.dispatch.planner._get_llm", lambda: mock_llm
        )
        state = {"user_prompt": "test", "working_directory": "."}
        result = plan_tasks(state)
        # Invalid agent should be replaced with an available one
        assert result["plan"][0]["agent"] == "gemini"


class TestReplanTasks:
    def test_exceeds_max_replans_aborts(self, monkeypatch):
        state = {
            "user_prompt": "test",
            "replan_count": 2,
            "max_replans": 2,
            "step_results": [],
        }
        result = replan_tasks(state)
        assert result["done"] is True
        assert result["abort"] is True

    def test_replans_with_context(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
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
                {"step_id": "step-1", "agent": "gemini", "status": "error", "error": "failed"}
            ],
        }
        result = replan_tasks(state)
        assert result["replan_count"] == 1
        assert len(result["plan"]) >= 1
