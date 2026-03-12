from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_config.doctor import _vendor_observability_checks
from ai_config.vendor.models import PROVENANCE_FILENAME, VendorImportSpec, VendorProvenance
from ai_config.vendor.skill_vendor import import_skill_repo


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


def _init_git_repo_root(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-b", "main")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "user.email", "test@example.com")
    _write(path / ".gitignore", "skills/external/*\n!skills/external/.gitkeep\n")
    _write(path / "skills" / "external" / ".gitkeep", "")
    _write(path / "config" / "master" / "ai-sync.yaml", "targets: {}\nmcp_servers: {}\n")
    (path / "inventory").mkdir(parents=True, exist_ok=True)
    _run_git(path, "add", ".")
    _run_git(path, "commit", "-m", "Initial commit")
    return path


def _write_vendor_manifest(repo_root: Path, *, sources: dict[str, dict[str, str]]) -> None:
    lines = ['version: "1.0.0"', "", "sources:"]
    for name, cfg in sources.items():
        lines.extend(
            [
                f"  {name}:",
                f'    source_url: "{cfg["source_url"]}"',
                f'    local_name: "{cfg.get("local_name", name)}"',
                f'    branch: "{cfg.get("branch", "main")}"',
            ]
        )
        if "ref" in cfg:
            lines.append(f'    ref: "{cfg["ref"]}"')
    lines.append("")
    _write(repo_root / "config" / "vendor_skills.yaml", "\n".join(lines))


def _write_index(repo_root: Path, records: list[dict[str, object]]) -> None:
    _write(repo_root / ".index" / "summary.json", json.dumps({"index_format_version": 3}, ensure_ascii=False))
    _write(repo_root / ".index" / "records.json", json.dumps(records, ensure_ascii=False, indent=2))


def test_vendor_observability_checks_pass_with_extra_local(tmp_path: Path) -> None:
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
    _write_index(
        repo_root,
        [
            {
                "id": "skill:demo",
                "name": "demo",
                "source_path": "skills/external/demo/demo/SKILL.md",
            }
        ],
    )

    results = {result.name: result for result in _vendor_observability_checks(repo_root)}
    assert results["vendor_manifest"].status == "pass"
    assert results["vendor_materialization"].status == "pass"
    assert results["vendor_git_hygiene"].status == "pass"
    assert results["vendor_index_presence"].status == "pass"
    assert results["vendor_extra_local"].status == "pass"
    assert results["vendor_extra_local"].details["entries"] == ["extra-local"]
    assert results["vendor_unmanaged_local"].status == "pass"


def test_vendor_observability_checks_fail_for_unmanaged_and_missing_provenance(tmp_path: Path) -> None:
    repo_root = _init_git_repo_root(tmp_path / "repo")
    _write_vendor_manifest(
        repo_root,
        sources={
            "missing-provenance": {
                "source_url": "https://example.com/missing-provenance.git",
                "local_name": "missing-provenance",
                "branch": "main",
                "ref": "1234567890abcdef",
            }
        },
    )
    _write(
        repo_root / "skills" / "external" / "missing-provenance" / "missing-provenance" / "SKILL.md",
        "---\nname: missing-provenance\ndescription: missing provenance\n---\n# Missing\n",
    )
    _write(
        repo_root / "skills" / "external" / "manual-local" / "manual-local" / "SKILL.md",
        "---\nname: manual-local\ndescription: manual\n---\n# Manual\n",
    )
    _write_index(
        repo_root,
        [
            {
                "id": "skill:missing-provenance",
                "name": "missing-provenance",
                "source_path": "skills/external/missing-provenance/missing-provenance/SKILL.md",
            }
        ],
    )

    results = {result.name: result for result in _vendor_observability_checks(repo_root)}
    assert results["vendor_manifest"].status == "pass"
    assert results["vendor_materialization"].status == "fail"
    assert results["vendor_unmanaged_local"].status == "fail"
    assert results["vendor_unmanaged_local"].details["entries"] == ["manual-local"]
    assert results["vendor_extra_local"].status == "pass"


def test_vendor_observability_checks_fail_for_manifest_without_ref(tmp_path: Path) -> None:
    repo_root = _init_git_repo_root(tmp_path / "repo")
    _write_vendor_manifest(
        repo_root,
        sources={
            "unpinned": {
                "source_url": "https://example.com/unpinned.git",
                "local_name": "unpinned",
                "branch": "main",
            }
        },
    )

    results = {result.name: result for result in _vendor_observability_checks(repo_root)}
    assert results["vendor_manifest"].status == "fail"
    assert "missing ref" in results["vendor_manifest"].details["errors"][0]
    assert results["vendor_materialization"].status == "fail"
