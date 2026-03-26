from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ai_config.contracts.approved_plan import (
    ApprovedPlan,
    ApprovedPlanExecutionRequest,
    PlanStep,
    ToolReference,
)
from ai_config.executor.plan_boundary import DispatchCLIPlanExecutor


def _request(tmp_path: Path) -> ApprovedPlanExecutionRequest:
    tool_ref = ToolReference(
        tool_id="skill:demo",
        tool_kind="skill",
        name="demo",
        source_path="skills/shared/demo/SKILL.md",
        selection_reason="approved",
        invoke_summary="skill_markdown: skills/shared/demo/SKILL.md",
        confidence=0.8,
    )
    plan = ApprovedPlan(
        user_goal="Open the demo skill",
        candidate_tools=[tool_ref],
        steps=[
            PlanStep(
                step_id="step-1",
                title="Open demo",
                purpose="Read the demo skill",
                inputs=["demo"],
                expected_output="content preview",
                tool_ref=tool_ref,
                depends_on=[],
            )
        ],
    )
    return ApprovedPlanExecutionRequest(
        plan=plan,
        repo_root=str(tmp_path),
        working_directory=str(tmp_path),
        tool_records=[{"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}],
        max_retries=1,
        parallel=False,
        keep_context=False,
    )


def test_dispatch_cli_plan_executor_uses_stable_json_boundary(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    captured: dict[str, object] = {}

    def _fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        request_path = Path(command[command.index("--execute-approved-plan") + 1])
        captured["payload"] = json.loads(request_path.read_text(encoding="utf-8"))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-1",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "success",
                    "final_report": "ok",
                    "step_results": [{"step_id": "step-1", "status": "success"}],
                    "error": None,
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    result = executor.execute_request(request)

    command = captured["command"]
    assert isinstance(command, list)
    assert "--execute-approved-plan" in command
    assert "--json" in command
    assert captured["payload"]["kind"] == "ai-config.approved-plan-execution-request"
    assert captured["payload"]["schema_version"] == "1.0.0"
    assert result["kind"] == "ai-config.approved-plan-execution-result"
    assert result["execution_id"] == "exec-1"
    assert result["status"] == "success"
    assert result["final_report"] == "ok"


def test_dispatch_cli_plan_executor_rejects_invalid_result_contract(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)

    def _fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"status": "success", "final_report": "ok"}, ensure_ascii=False),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    result = executor.execute_request(request)

    assert result["status"] == "error"
    assert "invalid execution result payload" in str(result["error"]).lower()


def test_dispatch_cli_plan_executor_accepts_structured_error_result(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)

    def _fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            1,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-2",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "error",
                    "final_report": "failed",
                    "step_results": [{"step_id": "step-1", "status": "error", "error": "boom"}],
                    "error": "boom",
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="boom",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    result = executor.execute_request(request)

    assert result["status"] == "error"
    assert result["execution_id"] == "exec-2"
    assert result["error"] == "boom"


def test_dispatch_cli_plan_executor_prefers_external_repo_checkout(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    captured: dict[str, object] = {}

    external_repo = tmp_path / "ai-config-dispatch"
    (external_repo / "src" / "ai_config_dispatch").mkdir(parents=True)
    (external_repo / "pyproject.toml").write_text("[project]\nname='ai-config-dispatch'\n", encoding="utf-8")
    (external_repo / "src" / "ai_config_dispatch" / "cli.py").write_text("def main():\n    pass\n", encoding="utf-8")

    def _fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-ext",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "success",
                    "final_report": "ok",
                    "step_results": [{"step_id": "step-1", "status": "success"}],
                    "error": None,
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path / "repo")
    monkeypatch.setattr(executor, "_external_repo_root", lambda: external_repo)

    result = executor.execute_request(request)

    command = captured["command"]
    assert command[:3] == [executor._command_prefix()[0], "-m", "ai_config_dispatch.cli"]
    env = captured["env"]
    assert isinstance(env, dict)
    assert str(external_repo / "src") in str(env.get("PYTHONPATH", ""))
    assert "exec-ext" == result["execution_id"]


def test_dispatch_cli_plan_executor_production_mode_ignores_sibling_checkout(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    captured: dict[str, object] = {}

    external_repo = tmp_path / "ai-config-dispatch"
    (external_repo / "src" / "ai_config_dispatch").mkdir(parents=True)
    (external_repo / "pyproject.toml").write_text("[project]\nname='ai-config-dispatch'\n", encoding="utf-8")
    (external_repo / "src" / "ai_config_dispatch" / "cli.py").write_text("def main():\n    pass\n", encoding="utf-8")

    monkeypatch.setenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "production")
    monkeypatch.setattr("ai_config.executor.plan_boundary.shutil.which", lambda name: "/usr/local/bin/ai-config-dispatch" if name == "ai-config-dispatch" else None)

    def _fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-prod",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "success",
                    "final_report": "ok",
                    "step_results": [{"step_id": "step-1", "status": "success"}],
                    "error": None,
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path / "repo")
    monkeypatch.setattr(executor, "_external_repo_root", lambda: external_repo)

    result = executor.execute_request(request)

    assert captured["command"] == ["/usr/local/bin/ai-config-dispatch", "--execute-approved-plan", captured["command"][2], "--json"]
    assert captured["env"] is None
    assert result["execution_id"] == "exec-prod"


def test_dispatch_cli_plan_executor_uses_installed_module_in_production(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    captured: dict[str, object] = {}

    monkeypatch.setenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "production")
    monkeypatch.setattr("ai_config.executor.plan_boundary.shutil.which", lambda _: None)

    def _fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-module",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "success",
                    "final_report": "ok",
                    "step_results": [{"step_id": "step-1", "status": "success"}],
                    "error": None,
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    monkeypatch.setattr(executor, "_external_repo_root", lambda: None)
    monkeypatch.setattr(executor, "_installed_module_command", lambda: [sys.executable, "-m", "ai_config_dispatch.cli"])

    result = executor.execute_request(request)

    assert captured["command"][:3] == [sys.executable, "-m", "ai_config_dispatch.cli"]
    assert captured["env"] is None
    assert result["execution_id"] == "exec-module"


def test_dispatch_cli_plan_executor_requires_explicit_in_repo_fallback(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)

    monkeypatch.setenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "local")
    monkeypatch.delenv("AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK", raising=False)
    monkeypatch.setattr("ai_config.executor.plan_boundary.shutil.which", lambda _: None)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    monkeypatch.setattr(executor, "_external_repo_root", lambda: None)
    monkeypatch.setattr(executor, "_installed_module_command", lambda: None)

    result = executor.execute_request(request)

    assert result["status"] == "error"
    assert "AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK=1" in str(result["error"])


def test_dispatch_cli_plan_executor_allows_explicit_in_repo_fallback(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    captured: dict[str, object] = {}

    monkeypatch.setenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "local")
    monkeypatch.setenv("AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK", "1")
    monkeypatch.setattr("ai_config.executor.plan_boundary.shutil.which", lambda _: None)

    def _fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "kind": "ai-config.approved-plan-execution-result",
                    "schema_version": "1.0.0",
                    "request_kind": "ai-config.approved-plan-execution-request",
                    "request_schema_version": "1.0.0",
                    "plan_id": request.plan.plan_id,
                    "plan_revision": request.plan.revision,
                    "execution_id": "exec-fallback",
                    "runtime": {"name": "ai-config-dispatch", "transport": "subprocess_json"},
                    "status": "success",
                    "final_report": "ok",
                    "step_results": [{"step_id": "step-1", "status": "success"}],
                    "error": None,
                    "replan_request": None,
                },
                ensure_ascii=False,
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    monkeypatch.setattr(executor, "_external_repo_root", lambda: None)
    monkeypatch.setattr(executor, "_installed_module_command", lambda: None)

    result = executor.execute_request(request)

    assert captured["command"][:3] == [sys.executable, "-m", "ai_config.dispatch.cli"]
    assert result["execution_id"] == "exec-fallback"


def test_dispatch_cli_plan_executor_rejects_invalid_runtime_mode(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    monkeypatch.setenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "staging")

    executor = DispatchCLIPlanExecutor(repo_root=tmp_path)
    result = executor.execute_request(request)

    assert result["status"] == "error"
    assert "AI_CONFIG_DISPATCH_RUNTIME_MODE" in str(result["error"])
