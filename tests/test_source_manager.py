"""Tests for source_manager module."""

from __future__ import annotations

import ai_config.source_manager as source_manager
from pathlib import Path

import pytest

from ai_config.source_manager import load_manifest, list_sources, main, sync_sources


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


SAMPLE_MANIFEST = """\
version: "1.0.0"

sources:
  test-skill:
    type: skill
    url: https://github.com/example/test-skill
    path: skills/external/test-skill
    branch: main

  anthropics-skills:
    type: skill
    url: https://github.com/anthropics/skills
    path: skills/external/anthropics-skills
    branch: main

  anthropics-knowledge-work-plugins:
    type: skill
    url: https://github.com/anthropics/knowledge-work-plugins
    path: skills/external/anthropics-knowledge-work-plugins
    branch: main

  antigravity-awesome-skills:
    type: skill
    url: https://github.com/sickn33/antigravity-awesome-skills
    path: skills/external/antigravity-awesome-skills
    branch: main

  nextlevelbuilder-ui-ux-pro-max-skill:
    type: skill
    url: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
    path: skills/external/nextlevelbuilder-ui-ux-pro-max-skill
    branch: main

  test-mcp:
    type: mcp
    url: https://github.com/example/test-mcp
    path: mcp/external/test-mcp
    branch: develop
"""


def test_load_manifest_parses_sources(tmp_path: Path) -> None:
    _write(tmp_path / "config/sources.yaml", SAMPLE_MANIFEST)

    manifest = load_manifest(tmp_path)
    assert manifest.version == "1.0.0"
    assert len(manifest.sources) == 6

    skill = next(s for s in manifest.sources if s.name == "test-skill")
    assert skill.source_type == "skill"
    assert skill.url == "https://github.com/example/test-skill"
    assert skill.path == "skills/external/test-skill"
    assert skill.branch == "main"

    mcp = next(s for s in manifest.sources if s.name == "test-mcp")
    assert mcp.source_type == "mcp"
    assert mcp.branch == "develop"


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    manifest = load_manifest(tmp_path)
    assert manifest.version == "1.0.0"
    assert manifest.sources == []


def test_load_manifest_empty_file(tmp_path: Path) -> None:
    _write(tmp_path / "config/sources.yaml", "")
    manifest = load_manifest(tmp_path)
    assert manifest.sources == []


def test_list_sources_marks_skills_as_delegated(tmp_path: Path) -> None:
    _write(tmp_path / "config/sources.yaml", SAMPLE_MANIFEST)

    rows = list_sources(tmp_path)
    assert len(rows) == 6
    status_by_name = {row["name"]: row["status"] for row in rows}
    assert status_by_name["test-skill"] == "delegated"
    assert status_by_name["anthropics-skills"] == "delegated"
    assert status_by_name["anthropics-knowledge-work-plugins"] == "delegated"
    assert status_by_name["antigravity-awesome-skills"] == "delegated"
    assert status_by_name["nextlevelbuilder-ui-ux-pro-max-skill"] == "delegated"
    assert status_by_name["test-mcp"] == "pending"


def test_sync_sources_only_manages_mcp_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / "config/sources.yaml", SAMPLE_MANIFEST)

    added: list[str] = []

    monkeypatch.setattr(source_manager, "_existing_submodule_paths", lambda repo_root: set())
    monkeypatch.setattr(source_manager, "_add_submodule", lambda repo_root, entry: added.append(entry.name) or True)

    result = sync_sources(tmp_path)
    assert result["added"] == ["mcp/external/test-mcp"]
    assert result["updated"] == []
    assert result["removed"] == []
    assert added == ["test-mcp"]


def test_add_skill_source_is_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--repo-root",
                str(tmp_path),
                "add",
                "demo-skill",
                "https://github.com/example/demo-skill",
                "--type",
                "skill",
            ]
        )

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "ai-config-vendor-skills" in captured.out


def test_remove_skill_source_only_cleans_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path / "config/sources.yaml", SAMPLE_MANIFEST)
    skill_dir = tmp_path / "skills" / "external" / "test-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)

    main(["--repo-root", str(tmp_path), "remove", "test-skill"])

    captured = capsys.readouterr()
    manifest_text = (tmp_path / "config" / "sources.yaml").read_text(encoding="utf-8")
    assert "test-skill" not in manifest_text
    assert skill_dir.exists()
    assert "skills/external files are unchanged" in captured.out
