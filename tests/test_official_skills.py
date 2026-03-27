from __future__ import annotations

import json
import subprocess
from pathlib import Path

import ai_config.official_skills as official_skills
from ai_config.official_skills import OFFICIAL_STATE_REL, build_official_status, sync_official_skills
from ai_config.registry.skill_parser import scan_skills


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


def _minimal_repo_root(path: Path) -> Path:
    _write(path / "config" / "master" / "ai-sync.yaml", "targets: {}\nmcp_servers: {}\n")
    _write(path / ".gitignore", "skills/external/*\n!skills/external/.gitkeep\n")
    _write(path / "skills" / "external" / ".gitkeep", "")
    return path


def _write_official_manifest(repo_root: Path, entries: list[dict[str, str]]) -> None:
    lines = [
        'version: "1.0.0"',
        'captured_at: "2026-03-27"',
        'source_url: "https://skills.sh/official"',
        "",
        "sources:",
    ]
    for entry in entries:
        lines.extend(
            [
                f'  - creator: "{entry["creator"]}"',
                f'    repo: "{entry["repo"]}"',
                f'    github_url: "{entry["github_url"]}"',
                f'    source_key: "{entry["creator"]}__{entry["repo"]}"',
            ]
        )
    _write(repo_root / "config" / "skills_sh_official.yaml", "\n".join(lines) + "\n")


def _write_vendor_manifest(repo_root: Path, entries: list[tuple[str, str]]) -> None:
    lines = ['version: "1.0.0"', "", "sources:"]
    for creator, repo in entries:
        name = f"{creator}-{repo}".replace("/", "-")
        lines.extend(
            [
                f"  {name}:",
                f'    source_url: "https://github.com/{creator}/{repo}"',
                f'    local_name: "{name}"',
                '    branch: "main"',
                '    ref: "deadbeef"',
            ]
        )
    _write(repo_root / "config" / "vendor_skills.yaml", "\n".join(lines) + "\n")


def test_build_official_status_counts_exact_only(tmp_path: Path) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "demo",
                "repo": "skills",
                "github_url": "https://github.com/demo/skills",
            },
            {
                "creator": "streamlit",
                "repo": "agent-skills",
                "github_url": "https://github.com/streamlit/agent-skills",
            },
            {
                "creator": "google-gemini",
                "repo": "gemini-skills",
                "github_url": "https://github.com/google-gemini/gemini-skills",
            },
        ],
    )
    _write_vendor_manifest(repo_root, [("streamlit", "agent-skills")])
    _write(
        repo_root / "skills" / "imported" / "skills-sh" / "sources" / "demo__skills" / "demo" / "SKILL.md",
        "---\nname: demo\ndescription: demo\n---\n# Demo\n",
    )
    _write(
        repo_root
        / "skills"
        / "imported"
        / "skills-sh"
        / "sources"
        / "google-gemini__gemini-cli"
        / "gemini-api-dev"
        / "SKILL.md",
        "---\nname: gemini-api-dev\ndescription: alias only\n---\n# Alias\n",
    )

    report = build_official_status(repo_root)

    assert report.total_sources == 3
    assert report.covered_exact == 2
    assert report.covered_in_imported == 1
    assert report.covered_in_vendor == 1
    assert report.missing_exact == 1
    assert report.missing_pairs == ["google-gemini/gemini-skills"]


def test_sync_official_skills_dry_run_reports_missing_without_mutation(tmp_path: Path) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "apify",
                "repo": "agent-skills",
                "github_url": "https://github.com/apify/agent-skills",
            }
        ],
    )

    status, results = sync_official_skills(repo_root, dry_run=True)

    assert status.missing_exact == 1
    assert results[0].status == "dry_run"
    assert not (repo_root / "skills" / "imported" / "skills-sh" / "sources" / "apify__agent-skills").exists()
    assert not (repo_root / OFFICIAL_STATE_REL).exists()


def test_sync_official_skills_imports_nested_hidden_skill_locations_and_writes_meta(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            ".claude/skills/alpha/SKILL.md": "---\nname: alpha\ndescription: alpha\n---\n# Alpha\n",
            ".agents/skills/beta/SKILL.md": "---\nname: beta\ndescription: beta\n---\n# Beta\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "demo",
                "repo": "hidden-skills",
                "github_url": str(upstream),
            }
        ],
    )

    status, results = sync_official_skills(repo_root)

    alpha_dir = repo_root / "skills" / "imported" / "skills-sh" / "sources" / "demo__hidden-skills" / "alpha"
    beta_dir = repo_root / "skills" / "imported" / "skills-sh" / "sources" / "demo__hidden-skills" / "beta"
    alpha_meta = json.loads((alpha_dir / ".skills-sh-meta.json").read_text(encoding="utf-8"))
    beta_meta = json.loads((beta_dir / ".skills-sh-meta.json").read_text(encoding="utf-8"))

    assert status.missing_exact == 0
    assert results[0].status == "imported"
    assert alpha_meta["sourcePath"] == ".claude/skills/alpha"
    assert beta_meta["sourcePath"] == ".agents/skills/beta"
    assert alpha_meta["origin"] == "skills.sh/official"
    assert beta_meta["sourceCommit"]


def test_sync_official_skills_skips_exact_vendor_coverage(tmp_path: Path) -> None:
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "streamlit",
                "repo": "agent-skills",
                "github_url": "https://github.com/streamlit/agent-skills",
            }
        ],
    )
    _write_vendor_manifest(repo_root, [("streamlit", "agent-skills")])

    status, results = sync_official_skills(repo_root)

    assert status.covered_exact == 1
    assert status.missing_exact == 0
    assert results == []
    assert not (repo_root / "skills" / "imported" / "skills-sh" / "sources" / "streamlit__agent-skills").exists()


def test_sync_official_skills_fails_for_repo_without_skill_files(tmp_path: Path) -> None:
    upstream = _init_git_repo(tmp_path / "upstream", {"README.md": "# No skills\n"})
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "demo",
                "repo": "no-skills",
                "github_url": str(upstream),
            }
        ],
    )

    status, results = sync_official_skills(repo_root)

    assert status.missing_exact == 1
    assert results[0].status == "failed"
    assert not (repo_root / "skills" / "imported" / "skills-sh" / "sources" / "demo__no-skills").exists()
    state = json.loads((repo_root / OFFICIAL_STATE_REL).read_text(encoding="utf-8"))
    assert state["results"][0]["status"] == "failed"


def test_sync_official_skills_records_clone_failures_and_continues(tmp_path: Path, monkeypatch) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha\n---\n# Alpha\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "demo",
                "repo": "broken",
                "github_url": "https://github.com/demo/broken",
            },
            {
                "creator": "demo",
                "repo": "skills",
                "github_url": str(upstream),
            },
        ],
    )

    real_clone_source = official_skills.clone_source

    def fake_clone_source(
        source: str,
        *,
        branch: str | None,
        ref: str | None,
        shallow: bool = False,
        archive_fallback: bool = False,
        clone_timeout: float | None = None,
    ):
        if source == "https://github.com/demo/broken":
            raise subprocess.CalledProcessError(128, ["git", "clone"], stderr="fatal: missing repo")
        return real_clone_source(
            source,
            branch=branch,
            ref=ref,
            shallow=shallow,
            archive_fallback=archive_fallback,
            clone_timeout=clone_timeout,
        )

    monkeypatch.setattr(official_skills, "clone_source", fake_clone_source)

    status, results = sync_official_skills(repo_root)

    assert status.covered_exact == 1
    assert status.missing_exact == 1
    assert [result.status for result in results] == ["failed", "imported"]
    assert results[0].error == "fatal: missing repo"
    assert results[1].pair == "demo/skills"
    state = json.loads((repo_root / OFFICIAL_STATE_REL).read_text(encoding="utf-8"))
    assert [item["status"] for item in state["results"]] == ["failed", "imported"]


def test_sync_official_skills_creates_imported_records_visible_to_scan(tmp_path: Path) -> None:
    upstream = _init_git_repo(
        tmp_path / "upstream",
        {
            "alpha/SKILL.md": "---\nname: alpha\ndescription: alpha\n---\n# Alpha\n",
        },
    )
    repo_root = _minimal_repo_root(tmp_path / "repo")
    _write_official_manifest(
        repo_root,
        [
            {
                "creator": "demo",
                "repo": "skills",
                "github_url": str(upstream),
            }
        ],
    )

    sync_official_skills(repo_root)
    records = scan_skills(repo_root)
    record = next(item for item in records if item.id == "skill:alpha")

    assert record.metadata["layer"] == "imported"
    assert record.metadata["source_repo"] == "demo__skills"
    assert record.source_path == "skills/imported/skills-sh/sources/demo__skills/alpha/SKILL.md"
