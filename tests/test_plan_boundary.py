from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_config.contracts.approved_plan import ApprovedPlan, ApprovedPlanExecutionRequest, PlanStep, ToolReference
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
            stdout=json.dumps({"status": "success", "final_report": "ok"}, ensure_ascii=False),
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
    assert result["status"] == "success"
    assert result["final_report"] == "ok"
