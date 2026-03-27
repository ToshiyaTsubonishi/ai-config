from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.vendor.models import PROVENANCE_FILENAME, VendorImportSpec, VendorProvenance
from ai_config.vendor.skill_vendor import (
    VendorError,
    bootstrap_legacy_imports,
    cleanup_legacy_submodules,
    import_skill_repo,
    inspect_vendor_state,
    sync_skills_sh_official,
    sync_vendor_manifest,
    update_imported_skills,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
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


def _init_git_repo_root(path: Path) -> Path:
    repo_root = _minimal_repo_root(path)
    _run_git(repo_root, "init", "-b", "main")
    _run_git(repo_root, "config", "user.name", "Test User")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    _write(repo_root / ".gitignore", "skills/external/*\n!skills/external/.gitkeep\n")
    _write(repo_root / "skills" / "external" / ".gitkeep", "")
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "Initial commit")
    return repo_root


def _write_vendor_manifest(repo_root: Path, *, sources: dict[str, dict[str, str]]) -> None:
    payload: dict[str, object] = {"version": "1.0.0", "sources": {}}
    sources_payload = payload["sources"]
    assert isinstance(sources_payload, dict)
    for name, cfg in sources.items():
        entry = {
            "source_url": cfg["source_url"],
            "local_name": cfg.get("local_name", name),
            "branch": cfg.get("branch", "main"),
        }
        if "ref" in cfg:
            entry["ref"] = cfg["ref"]
        sources_payload[name] = entry
    _write(
        repo_root / "config" / "vendor_skills.yaml",
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
    )


def test_import_skill_repo_force_reimport_preserves_imported_at_and_requested_ref(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha skill\n---\n# Alpha\n",
            "alpha/scripts/run.py": "print('alpha')\n",
        },
    )
    ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _minimal_repo_root(tmp_path / "repo")

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T00:00:00Z"):
        first = import_skill_repo(
            VendorImportSpec(source_url=str(upstream), local_name="demo", branch="main", ref=ref),
            repo_root=repo_root,
        )

    provenance_path = repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME
    first_provenance = VendorProvenance.from_path(provenance_path)

    assert first.status == "imported"
    assert first.skill_count == 1
    assert first_provenance.imported_at == "2026-03-12T00:00:00Z"
    assert first_provenance.updated_at == "2026-03-12T00:00:00Z"
    assert first_provenance.requested_ref == ref
    assert (repo_root / "skills" / "external" / "demo" / "alpha" / "scripts" / "run.py").exists()

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T01:00:00Z"):
        second = import_skill_repo(
            VendorImportSpec(source_url=str(upstream), local_name="demo", branch="main", ref=ref, force=True),
            repo_root=repo_root,
        )

    second_provenance = VendorProvenance.from_path(provenance_path)
    assert second.status == "updated"
    assert second_provenance.imported_at == "2026-03-12T00:00:00Z"
    assert second_provenance.updated_at == "2026-03-12T01:00:00Z"
    assert second_provenance.requested_ref == ref


def test_update_imported_skills_respects_requested_ref_pin(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha skill v1\n---\n# Alpha\n",
        },
    )
    pinned_ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _minimal_repo_root(tmp_path / "repo")

    import_skill_repo(
        VendorImportSpec(source_url=str(upstream), local_name="demo", branch="main", ref=pinned_ref),
        repo_root=repo_root,
    )

    _write(upstream / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: alpha skill v2\n---\n# Alpha\n")
    _commit_all(upstream, "Advance main")

    results = update_imported_skills(repo_root=repo_root, local_name="demo")

    result = results[0]
    provenance = VendorProvenance.from_path(repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME)
    assert result.status == "up_to_date"
    assert provenance.commit_sha == pinned_ref
    assert provenance.requested_ref == pinned_ref


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

    shutil.rmtree(upstream / "beta")
    _write(upstream / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: alpha skill updated\n---\n# Alpha\n")
    _commit_all(upstream, "Remove beta")

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T02:00:00Z"):
        results = update_imported_skills(repo_root=repo_root, local_name="demo")

    result = results[0]
    provenance = VendorProvenance.from_path(repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME)
    assert result.status == "updated"
    assert result.orphaned_dirs == ["beta"]
    assert provenance.original_paths == ["alpha/SKILL.md"]
    assert not (repo_root / "skills" / "external" / "demo" / "beta").exists()


def test_sync_vendor_manifest_requires_exact_ref(tmp_path: Path) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": "https://github.com/example/demo.git",
                "local_name": "demo",
                "branch": "main",
            }
        },
    )

    with pytest.raises(VendorError, match="must pin an exact ref"):
        sync_vendor_manifest(repo_root=repo_root)


def test_sync_vendor_manifest_materializes_pinned_ref_and_prunes_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "demo/SKILL.md": "---\nname: demo-skill\ndescription: demo searchable skill\n---\n# Demo\n",
        },
    )
    ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": str(upstream),
                "local_name": "demo",
                "branch": "main",
                "ref": ref,
            }
        },
    )

    extra_dir = repo_root / "skills" / "external" / "extra"
    _write(extra_dir / "extra" / "SKILL.md", "---\nname: extra\ndescription: extra skill\n---\n# Extra\n")
    VendorProvenance(
        schema_version=1,
        source_url="https://example.com/extra.git",
        branch="main",
        requested_ref="deadbeef",
        commit_sha="deadbeef",
        original_paths=["extra/SKILL.md"],
        imported_at="2026-03-12T00:00:00Z",
        updated_at="2026-03-12T00:00:00Z",
        import_tool="test",
        skill_count=1,
        local_name="extra",
    ).write(extra_dir / PROVENANCE_FILENAME)

    results = sync_vendor_manifest(repo_root=repo_root)
    statuses = {result.local_name: result.status for result in results}
    demo_provenance = VendorProvenance.from_path(repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME)
    assert statuses["demo"] == "imported"
    assert extra_dir.exists()
    assert demo_provenance.requested_ref == ref

    with patch("ai_config.vendor.skill_vendor.import_skill_repo", side_effect=AssertionError("unexpected import")):
        aligned = sync_vendor_manifest(repo_root=repo_root)
    assert aligned[0].status == "up_to_date"

    dry_run = sync_vendor_manifest(repo_root=repo_root, prune=True, dry_run=True)
    assert any(result.local_name == "extra" and result.message.startswith("Would prune") for result in dry_run)
    assert extra_dir.exists()

    pruned = sync_vendor_manifest(repo_root=repo_root, prune=True)
    assert any(result.local_name == "extra" and result.status == "pruned" for result in pruned)
    assert not extra_dir.exists()

    monkeypatch.undo()


def test_sync_vendor_manifest_aligns_bootstrapped_provenance_without_reimport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    demo_dir = repo_root / "skills" / "external" / "demo"
    _write(demo_dir / "demo" / "SKILL.md", "---\nname: demo\ndescription: demo skill\n---\n# Demo\n")
    provenance = VendorProvenance(
        schema_version=1,
        source_url="https://example.com/demo.git",
        branch="main",
        requested_ref=None,
        commit_sha="abc123",
        original_paths=["demo/SKILL.md"],
        imported_at="2026-03-12T00:00:00Z",
        updated_at="2026-03-12T00:00:00Z",
        import_tool="ai-config-vendor-skills bootstrap-legacy",
        skill_count=1,
        local_name="demo",
    )
    provenance.write(demo_dir / PROVENANCE_FILENAME)
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": "https://example.com/demo.git",
                "local_name": "demo",
                "branch": "main",
                "ref": "abc123",
            }
        },
    )

    monkeypatch.setattr("ai_config.vendor.skill_vendor.import_skill_repo", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected import")))

    results = sync_vendor_manifest(repo_root=repo_root)
    aligned = VendorProvenance.from_path(demo_dir / PROVENANCE_FILENAME)
    assert results[0].status == "aligned"
    assert aligned.requested_ref == "abc123"


def test_sync_skills_sh_official_materializes_into_official_layer(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: official-alpha\ndescription: official alpha\n---\n# Alpha\n",
        },
    )
    ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write(
        repo_root / "config" / "skills_sh_official.yaml",
        yaml.safe_dump(
            {
                "version": "1.0.0",
                "sources": {
                    "demo": {
                        "source_url": str(upstream),
                        "local_name": "demo",
                        "branch": "main",
                        "ref": ref,
                    }
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    )

    results = sync_skills_sh_official(repo_root=repo_root)
    provenance = VendorProvenance.from_path(repo_root / "skills" / "official" / "demo" / PROVENANCE_FILENAME)

    assert results[0].status == "imported"
    assert provenance.import_tool == "ai-config-vendor-skills sync-skills-sh-official"
    assert provenance.requested_ref == ref
    assert (repo_root / "skills" / "official" / "demo" / "alpha" / "SKILL.md").exists()


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
\tpath = skills/external/legacy-demo
\turl = https://github.com/example/legacy-demo.git
\tbranch = main
""".strip()
        + "\n",
    )

    with patch("ai_config.vendor.skill_vendor._utc_now", return_value="2026-03-12T03:00:00Z"):
        results = bootstrap_legacy_imports(repo_root=repo_root, bootstrap_all=True)

    result = results[0]
    provenance = VendorProvenance.from_path(legacy_dir / PROVENANCE_FILENAME)
    assert result.status == "bootstrapped"
    assert result.source_url == "https://github.com/example/legacy-demo.git"
    assert provenance.import_tool == "ai-config-vendor-skills bootstrap-legacy"
    assert provenance.imported_at == "2026-03-12T03:00:00Z"
    assert provenance.original_paths == ["legacy/SKILL.md"]
    assert provenance.requested_ref is None


def test_cleanup_legacy_submodule_requires_provenance(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {"demo/SKILL.md": "---\nname: demo\ndescription: demo\n---\n# Demo\n"},
    )
    repo_root = _init_git_repo_root(tmp_path / "repo")
    _run_git(
        repo_root,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-f",
        str(upstream),
        "skills/external/demo",
    )

    results = cleanup_legacy_submodules(repo_root=repo_root, local_name="demo")
    assert results[0].status == "blocked"
    assert "Run bootstrap-legacy first" in results[0].message


def test_cleanup_legacy_submodule_dry_run_then_apply_preserves_payload(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {"demo/SKILL.md": "---\nname: demo\ndescription: demo\n---\n# Demo\n"},
    )
    repo_root = _init_git_repo_root(tmp_path / "repo")
    _run_git(
        repo_root,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-f",
        str(upstream),
        "skills/external/demo",
    )
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "Add demo submodule")

    bootstrap_legacy_imports(repo_root=repo_root, local_name="demo")

    dry_run = cleanup_legacy_submodules(repo_root=repo_root, local_name="demo")
    assert dry_run[0].status == "dry_run"
    assert (repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME).exists()

    cleaned = cleanup_legacy_submodules(repo_root=repo_root, local_name="demo", apply=True)
    assert cleaned[0].status == "cleaned"
    assert (repo_root / "skills" / "external" / "demo" / "demo" / "SKILL.md").exists() or (
        repo_root / "skills" / "external" / "demo" / "SKILL.md"
    ).exists()
    assert (repo_root / "skills" / "external" / "demo" / PROVENANCE_FILENAME).exists()
    assert not (repo_root / "skills" / "external" / "demo" / ".git").exists()
    assert not (repo_root / ".gitmodules").exists()

    ls_files = _run_git(repo_root, "ls-files", "--stage", "--", "skills/external/demo", check=False)
    assert "160000" not in (ls_files.stdout or "")

    all_results = cleanup_legacy_submodules(repo_root=repo_root, cleanup_all=True)
    assert all_results[0].status == "already_clean"


def test_inspect_vendor_state_classifies_manifest_and_local_entries(tmp_path: Path) -> None:
    repo_root = _init_git_repo_root(tmp_path / "repo")

    ready_upstream = _init_git_repo(
        tmp_path / "ready-upstream",
        {"ready/SKILL.md": "---\nname: ready\ndescription: ready\n---\n# Ready\n"},
    )
    ready_ref = _run_git(ready_upstream, "rev-parse", "HEAD").stdout.strip()
    import_skill_repo(
        VendorImportSpec(source_url=str(ready_upstream), local_name="ready", branch="main", ref=ready_ref),
        repo_root=repo_root,
    )

    align_upstream = _init_git_repo(
        tmp_path / "align-upstream",
        {"align/SKILL.md": "---\nname: align\ndescription: align\n---\n# Align\n"},
    )
    align_ref = _run_git(align_upstream, "rev-parse", "HEAD").stdout.strip()
    import_skill_repo(
        VendorImportSpec(source_url=str(align_upstream), local_name="align", branch="main", ref=align_ref),
        repo_root=repo_root,
    )
    align_provenance_path = repo_root / "skills" / "external" / "align" / PROVENANCE_FILENAME
    align_provenance = VendorProvenance.from_path(align_provenance_path)
    VendorProvenance(
        schema_version=align_provenance.schema_version,
        source_url=align_provenance.source_url,
        branch=align_provenance.branch,
        requested_ref=None,
        commit_sha=align_provenance.commit_sha,
        original_paths=align_provenance.original_paths,
        imported_at=align_provenance.imported_at,
        updated_at=align_provenance.updated_at,
        import_tool=align_provenance.import_tool,
        skill_count=align_provenance.skill_count,
        local_name=align_provenance.local_name,
    ).write(align_provenance_path)

    sync_upstream = _init_git_repo(
        tmp_path / "sync-upstream",
        {"sync/SKILL.md": "---\nname: sync\ndescription: sync\n---\n# Sync\n"},
    )
    old_sync_ref = _run_git(sync_upstream, "rev-parse", "HEAD").stdout.strip()
    import_skill_repo(
        VendorImportSpec(source_url=str(sync_upstream), local_name="sync", branch="main", ref=old_sync_ref),
        repo_root=repo_root,
    )
    _write(sync_upstream / "sync" / "SKILL.md", "---\nname: sync\ndescription: sync v2\n---\n# Sync\n")
    _commit_all(sync_upstream, "Advance sync")
    new_sync_ref = _run_git(sync_upstream, "rev-parse", "HEAD").stdout.strip()

    missing_provenance_dir = repo_root / "skills" / "external" / "missing-provenance"
    _write(
        missing_provenance_dir / "missing-provenance" / "SKILL.md",
        "---\nname: missing-provenance\ndescription: missing provenance\n---\n# Missing\n",
    )

    extra_dir = repo_root / "skills" / "external" / "extra-local"
    _write(extra_dir / "extra-local" / "SKILL.md", "---\nname: extra-local\ndescription: extra\n---\n# Extra\n")
    VendorProvenance(
        schema_version=1,
        source_url="https://example.com/extra-local.git",
        branch="main",
        requested_ref="deadbeef",
        commit_sha="deadbeef",
        original_paths=["extra-local/SKILL.md"],
        imported_at="2026-03-12T00:00:00Z",
        updated_at="2026-03-12T00:00:00Z",
        import_tool="test",
        skill_count=1,
        local_name="extra-local",
    ).write(extra_dir / PROVENANCE_FILENAME)

    unmanaged_dir = repo_root / "skills" / "external" / "manual-local"
    _write(unmanaged_dir / "manual-local" / "SKILL.md", "---\nname: manual-local\ndescription: manual\n---\n# Manual\n")

    _write_vendor_manifest(
        repo_root,
        sources={
            "ready": {
                "source_url": str(ready_upstream),
                "local_name": "ready",
                "branch": "main",
                "ref": ready_ref,
            },
            "align": {
                "source_url": str(align_upstream),
                "local_name": "align",
                "branch": "main",
                "ref": align_ref,
            },
            "sync": {
                "source_url": str(sync_upstream),
                "local_name": "sync",
                "branch": "main",
                "ref": new_sync_ref,
            },
            "missing": {
                "source_url": "https://example.com/missing.git",
                "local_name": "missing",
                "branch": "main",
                "ref": "1234567890abcdef",
            },
            "missing-provenance": {
                "source_url": "https://example.com/missing-provenance.git",
                "local_name": "missing-provenance",
                "branch": "main",
                "ref": "fedcba0987654321",
            },
        },
    )

    report = inspect_vendor_state(repo_root)
    status_by_name = {entry.local_name: entry.status for entry in report.entries}

    assert status_by_name["ready"] == "ready"
    assert status_by_name["align"] == "needs_align"
    assert status_by_name["sync"] == "needs_sync"
    assert status_by_name["missing"] == "missing"
    assert status_by_name["missing-provenance"] == "missing_provenance"
    assert status_by_name["extra-local"] == "extra_local"
    assert status_by_name["manual-local"] == "unmanaged_local"
    assert report.summary.total_manifest_entries == 5
    assert report.summary.ready == 1
    assert report.summary.needs_align == 1
    assert report.summary.needs_sync == 1
    assert report.summary.missing == 1
    assert report.summary.missing_provenance == 1
    assert report.summary.extra_local == 1
    assert report.summary.unmanaged_local == 1
    assert not report.manifest_errors
    assert all(entry.git_ignored for entry in report.entries)


def test_inspect_vendor_state_marks_legacy_submodule(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {"demo/SKILL.md": "---\nname: demo\ndescription: demo\n---\n# Demo\n"},
    )
    upstream_ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _init_git_repo_root(tmp_path / "repo")
    _run_git(
        repo_root,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-f",
        str(upstream),
        "skills/external/demo",
    )
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": str(upstream),
                "local_name": "demo",
                "branch": "main",
                "ref": upstream_ref,
            }
        },
    )

    report = inspect_vendor_state(repo_root)
    assert report.entries[0].status == "legacy_submodule"


def test_vendor_cli_status_json_schema(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {"demo/SKILL.md": "---\nname: demo\ndescription: demo\n---\n# Demo\n"},
    )
    ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _init_git_repo_root(tmp_path / "repo")
    import_skill_repo(
        VendorImportSpec(source_url=str(upstream), local_name="demo", branch="main", ref=ref),
        repo_root=repo_root,
    )
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": str(upstream),
                "local_name": "demo",
                "branch": "main",
                "ref": ref,
            }
        },
    )

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.vendor.cli",
            "--repo-root",
            str(repo_root),
            "status",
            "--json",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == 1
    assert payload["generated_at"].endswith("Z")
    assert payload["repo_root"] == str(repo_root.resolve())
    assert payload["summary"]["total_manifest_entries"] == 1
    assert payload["entries"][0]["status"] == "ready"


def test_vendor_cli_sync_manifest_and_index_search(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "demo/SKILL.md": "---\nname: demo-skill\ndescription: demo searchable skill\n---\n# Demo\n",
        },
    )
    ref = _run_git(upstream, "rev-parse", "HEAD").stdout.strip()
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_vendor_manifest(
        repo_root,
        sources={
            "demo": {
                "source_url": str(upstream),
                "local_name": "demo",
                "branch": "main",
                "ref": ref,
            }
        },
    )

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"

    sync_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.vendor.cli",
            "--repo-root",
            str(repo_root),
            "sync-manifest",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert sync_proc.returncode == 0, sync_proc.stderr
    assert "demo: imported" in sync_proc.stdout
    assert ref in sync_proc.stdout

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
