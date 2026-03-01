from __future__ import annotations

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
            "demo skill search",
            "--index-dir",
            str(index_dir),
            "--search-only",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert agent_proc.returncode == 0, agent_proc.stderr
    assert "demo-skill" in agent_proc.stdout.lower()
