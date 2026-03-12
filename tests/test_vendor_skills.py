from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.vendor.models import VendorImportSpec, VendorProvenance
from ai_config.vendor.skill_vendor import (
    bootstrap_legacy_imports,
    import_skill_repo,
    update_imported_skills,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_git_repo(path: Path, files: dict[str, str]) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-b", "main")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "user.email", "test@example.com")
    for rel_path, content in files.items():
        _write(path / rel_path, content)
    _run_git(path, "add", ".")
    _run_git(path, "commit", "-m", "Initial commit")
    return path


def _commit_all(path: Path, message: str) -> None:
    _run_git(path, "add", ".")
    _run_git(path, "commit", "-m", message)


def _minimal_repo_root(path: Path) -> Path:
    _write(
        path / "config" / "master" / "ai-sync.yaml",
        """
targets: {}
mcp_servers: {}
""".strip(),
    )
    (path / "inventory").mkdir(parents=True, exist_ok=True)
    return path


def test_import_skill_repo_force_reimport_preserves_imported_at(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha skill\n---\n# Alpha\n",
            "alpha/scripts/run.py": "print('alpha')\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T00:00:00Z"):
        first = import_skill_repo(
            VendorImportSpec(source_url=str(upstream), local_name="demo"),
            repo_root=repo_root,
        )

    provenance_path = repo_root / "skills" / "external" / "demo" / ".import.json"
    first_provenance = VendorProvenance.from_path(provenance_path)

    assert first.status == "imported"
    assert first.skill_count == 1
    assert first_provenance.imported_at == "2026-03-12T00:00:00Z"
    assert first_provenance.updated_at == "2026-03-12T00:00:00Z"
    assert (repo_root / "skills" / "external" / "demo" / "alpha" / "scripts" / "run.py").exists()

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T01:00:00Z"):
        second = import_skill_repo(
            VendorImportSpec(source_url=str(upstream), local_name="demo", force=True),
            repo_root=repo_root,
        )

    second_provenance = VendorProvenance.from_path(provenance_path)
    assert second.status == "updated"
    assert second_provenance.imported_at == "2026-03-12T00:00:00Z"
    assert second_provenance.updated_at == "2026-03-12T01:00:00Z"


def test_update_imported_skills_removes_orphans(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha skill\n---\n# Alpha\n",
            "beta/SKILL.md": "---\nname: beta\ndescription: beta skill\n---\n# Beta\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T00:00:00Z"):
        import_skill_repo(VendorImportSpec(source_url=str(upstream), local_name="demo"), repo_root=repo_root)

    beta_dir = upstream / "beta"
    shutil.rmtree(beta_dir)
    _write(upstream / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: alpha skill updated\n---\n# Alpha\n")
    _commit_all(upstream, "Remove beta")

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T02:00:00Z"):
        results = update_imported_skills(repo_root=repo_root, local_name="demo")

    result = results[0]
    provenance = VendorProvenance.from_path(repo_root / "skills" / "external" / "demo" / ".import.json")
    assert result.status == "updated"
    assert result.orphaned_dirs == ["beta"]
    assert provenance.original_paths == ["alpha/SKILL.md"]
    assert not (repo_root / "skills" / "external" / "demo" / "beta").exists()


def test_bootstrap_legacy_imports_backfills_provenance(tmp_path: Path) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    legacy_dir = _init_git_repo(
        repo_root / "skills" / "external" / "legacy-demo",
        {
            "legacy/SKILL.md": "---\nname: legacy-demo\ndescription: legacy skill\n---\n# Legacy\n",
        },
    )
    _write(
        repo_root / ".gitmodules",
        """
[submodule "skills/external/legacy-demo"]
	path = skills/external/legacy-demo
	url = https://github.com/example/legacy-demo.git
	branch = main
""".strip()
        + "\n",
    )

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T03:00:00Z"):
        results = bootstrap_legacy_imports(repo_root=repo_root, bootstrap_all=True)

    result = results[0]
    provenance = VendorProvenance.from_path(legacy_dir / ".import.json")
    assert result.status == "bootstrapped"
    assert result.source_url == "https://github.com/example/legacy-demo.git"
    assert provenance.import_tool == "ai-config-vendor-skills bootstrap-legacy"
    assert provenance.imported_at == "2026-03-12T03:00:00Z"
    assert provenance.original_paths == ["legacy/SKILL.md"]


def test_vendor_cli_bootstrap_update_and_index_search(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "demo/SKILL.md": "---\nname: demo-skill\ndescription: demo searchable skill\n---\n# Demo\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")
    external_dir = repo_root / "skills" / "external"
    external_dir.mkdir(parents=True, exist_ok=True)
    _run_git(external_dir, "clone", "--quiet", str(upstream), "demo")
    _write(
        repo_root / ".gitmodules",
        f"""
[submodule "skills/external/demo"]
	path = skills/external/demo
	url = {upstream}
	branch = main
""".strip()
        + "\n",
    )

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    bootstrap_proc = subprocess.run(
        [sys.executable, "-m", "ai_config.vendor.cli", "--repo-root", str(repo_root), "bootstrap-legacy", "--all"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert bootstrap_proc.returncode == 0, bootstrap_proc.stderr
    assert "demo: bootstrapped" in bootstrap_proc.stdout

    update_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.vendor.cli",
            "--repo-root",
            str(repo_root),
            "update",
            "--all",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert update_proc.returncode == 0, update_proc.stderr
    assert "demo: up_to_date" in update_proc.stdout

    index_dir = tmp_path / "index"
    build_proc = subprocess.run(
        [sys.executable, "-m", "ai_config.build_index", "--repo-root", str(repo_root), "--index-dir", str(index_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert build_proc.returncode == 0, build_proc.stderr

    retriever = HybridRetriever(index_dir)
    hits = retriever.search("demo searchable skill", top_k=5)
    assert hits
    assert any(hit.record.id == "skill:demo-skill" for hit in hits)
