from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_cli_smoke_build_and_search_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "src").mkdir(parents=True, exist_ok=True)

    _write(
        repo_root / "skills" / "shared" / "demo" / "SKILL.md",
        "---\nname: demo-skill\ndescription: demo searchable skill\n---\n# Demo\n",
    )
    _write(
        repo_root / "config" / "master" / "ai-sync.yaml",
        """
targets:
  codex:
    templates:
      config_template: "config/targets/codex/config.toml.tmpl"
mcp_servers: {}
""".strip(),
    )
    _write(repo_root / "config" / "targets" / "codex" / "config.toml.tmpl", "[mcp_servers.demo]\ncommand = \"npx\"\n")
    (repo_root / "inventory").mkdir(parents=True, exist_ok=True)

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    index_dir = tmp_path / "index"
    build_proc = subprocess.run(
        [sys.executable, "-m", "ai_config.build_index", "--repo-root", str(repo_root), "--index-dir", str(index_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert build_proc.returncode == 0, build_proc.stderr

    agent_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.orchestrator.cli",
            "search",
            "demo skill search",
            "--index-dir",
            str(index_dir),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert agent_proc.returncode == 0, agent_proc.stderr
    assert "demo-skill" in agent_proc.stdout.lower()


def test_cli_plan_only_and_execute_plan(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "src").mkdir(parents=True, exist_ok=True)

    _write(
        repo_root / "skills" / "shared" / "demo" / "SKILL.md",
        "---\nname: demo-skill\ndescription: demo searchable skill\n---\n# Demo\n",
    )
    _write(
        repo_root / "config" / "master" / "ai-sync.yaml",
        """
targets:
  codex:
    templates:
      config_template: "config/targets/codex/config.toml.tmpl"
mcp_servers: {}
""".strip(),
    )
    _write(repo_root / "config" / "targets" / "codex" / "config.toml.tmpl", "[mcp_servers.demo]\ncommand = \"npx\"\n")
    (repo_root / "inventory").mkdir(parents=True, exist_ok=True)

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    index_dir = tmp_path / "index"
    build_proc = subprocess.run(
        [sys.executable, "-m", "ai_config.build_index", "--repo-root", str(repo_root), "--index-dir", str(index_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert build_proc.returncode == 0, build_proc.stderr

    plan_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.orchestrator.cli",
            "plan",
            "demo skill search",
            "--index-dir",
            str(index_dir),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
    )
    assert plan_proc.returncode == 0, plan_proc.stderr
    assert "Plan ID:" in plan_proc.stdout
    assert '"plan_id"' in plan_proc.stdout

    plan_file = tmp_path / "approved-plan.json"
    plan_file.write_text(
        json.dumps(
            {
                "plan_id": "plan-cli",
                "revision": 1,
                "user_goal": "Open the demo skill",
                "assumptions": [],
                "specialist_route": "general",
                "candidate_tools": [
                    {
                        "tool_id": "skill:demo-skill",
                        "tool_kind": "skill",
                        "name": "demo-skill",
                        "source_path": "skills/shared/demo/SKILL.md",
                        "selection_reason": "approved",
                        "invoke_summary": "skill_markdown: skills/shared/demo/SKILL.md",
                        "confidence": 0.8,
                    }
                ],
                "steps": [
                    {
                        "step_id": "step-1",
                        "title": "Open demo",
                        "purpose": "Read the demo skill",
                        "inputs": ["demo"],
                        "expected_output": "content preview",
                        "tool_ref": {
                            "tool_id": "skill:demo-skill",
                            "tool_kind": "skill",
                            "name": "demo-skill",
                            "source_path": "skills/shared/demo/SKILL.md",
                            "selection_reason": "approved",
                            "invoke_summary": "skill_markdown: skills/shared/demo/SKILL.md",
                            "confidence": 0.8,
                        },
                        "depends_on": [],
                        "fallback_strategy": {"action": "abort", "fallback_tool_id": None, "notes": ""},
                        "action": "run",
                        "params": {},
                        "working_directory": ".",
                    }
                ],
                "approval_required": True,
                "execution_notes": "approved plan",
                "feasibility": "full",
                "notes": "approved plan",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    execute_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.orchestrator.cli",
            "execute-approved-plan",
            "--index-dir",
            str(index_dir),
            "--plan",
            str(plan_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
    )
    assert execute_proc.returncode == 0, execute_proc.stderr
    assert "Approved Plan Execution" in execute_proc.stdout


def test_build_index_default_profile_excludes_antigravity(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    _write(
        repo_root / "skills" / "external" / "anthropics-skills" / "skills" / "docx" / "SKILL.md",
        "---\nname: anthropic-docx\ndescription: anthropic skill\n---\n# docx\n",
    )
    _write(
        repo_root / "skills" / "external" / "antigravity-awesome-skills" / "skills" / "heavy" / "SKILL.md",
        "---\nname: antigravity-heavy\ndescription: antigravity skill\n---\n# heavy\n",
    )
    _write(
        repo_root / "config" / "master" / "ai-sync.yaml",
        """
targets: {}
mcp_servers: {}
""".strip(),
    )
    _write(
        repo_root / "config" / "index_profiles.yaml",
        """
version: "1.0.0"
profiles:
  default:
    include:
      - "**"
    exclude:
      - "skills/external/antigravity-awesome-skills/**"
  full:
    include:
      - "**"
    exclude: []
""".strip(),
    )
    (repo_root / "inventory").mkdir(parents=True, exist_ok=True)

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    index_dir = tmp_path / "index"
    build_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.build_index",
            "--repo-root",
            str(repo_root),
            "--index-dir",
            str(index_dir),
            "--profile",
            "default",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert build_proc.returncode == 0, build_proc.stderr

    records_json = json.loads((index_dir / "records.json").read_text(encoding="utf-8"))
    paths = [r["source_path"] for r in records_json]
    assert any("anthropics-skills" in p for p in paths)
    assert all("antigravity-awesome-skills" not in p for p in paths)
