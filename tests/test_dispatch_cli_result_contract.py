from __future__ import annotations

import json
from pathlib import Path

from ai_config.contracts.approved_plan import ApprovedPlan, ApprovedPlanExecutionRequest, PlanStep, ToolReference
from ai_config.dispatch import cli


def _request_file(tmp_path: Path) -> Path:
    tool_ref = ToolReference(
        tool_id="skill:demo",
        tool_kind="skill",
        name="demo",
        source_path="skills/shared/demo/SKILL.md",
        selection_reason="approved",
        invoke_summary="skill_markdown: skills/shared/demo/SKILL.md",
        confidence=0.8,
    )
    request = ApprovedPlanExecutionRequest(
        plan=ApprovedPlan(
            plan_id="plan-cli",
            revision=1,
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
        ),
        repo_root=str(tmp_path),
        working_directory=str(tmp_path),
        tool_records=[{"id": "skill:demo", "tool_kind": "skill", "name": "demo", "source_path": "skills/shared/demo/SKILL.md"}],
    )
    path = tmp_path / "approved-plan-request.json"
    path.write_text(json.dumps(request.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_dispatch_cli_emits_stable_execution_result_json(monkeypatch, tmp_path: Path, capsys) -> None:
    request_path = _request_file(tmp_path)

    class _FakeAgent:
        def invoke(self, _: dict[str, object]) -> dict[str, object]:
            return {
                "approved_plan": {
                    "plan_id": "plan-cli",
                    "revision": 1,
                },
                "done": True,
                "abort": False,
                "error": None,
                "final_report": "ok",
                "step_results": [{"step_id": "step-1", "status": "success", "agent": "tool_executor"}],
                "replan_request": None,
            }

    monkeypatch.setattr(cli, "create_dispatch_agent", lambda: _FakeAgent())
    monkeypatch.setattr(cli, "load_runtime_env", lambda: None)

    cli.main(["--execute-approved-plan", str(request_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "ai-config.approved-plan-execution-result"
    assert payload["schema_version"] == "1.0.0"
    assert payload["request_kind"] == "ai-config.approved-plan-execution-request"
    assert payload["plan_id"] == "plan-cli"
    assert payload["status"] == "success"
    assert payload["error"] is None
