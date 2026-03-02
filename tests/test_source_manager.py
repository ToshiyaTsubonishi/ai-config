"""Tests for source_manager module."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_config.source_manager import SourceEntry, SourceManifest, load_manifest, list_sources


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
    assert len(manifest.sources) == 2

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


def test_list_sources_shows_pending_status(tmp_path: Path) -> None:
    _write(tmp_path / "config/sources.yaml", SAMPLE_MANIFEST)

    rows = list_sources(tmp_path)
    assert len(rows) == 2
    # No git repo → all should be pending
    for row in rows:
        assert row["status"] == "pending"
    names = {r["name"] for r in rows}
    assert names == {"test-skill", "test-mcp"}
