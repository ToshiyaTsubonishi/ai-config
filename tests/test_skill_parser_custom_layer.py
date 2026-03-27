"""Tests for custom skill layer recognition in skill_parser."""

from __future__ import annotations

from pathlib import Path

from ai_config.registry.skill_parser import SKILL_LAYERS, parse_skill_file, scan_skills


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


SAMPLE_SKILL = """\
---
name: my-custom-tool
description: A custom tool for testing
---

# My Custom Tool

This is a custom skill.
"""


def test_custom_layer_in_skill_layers() -> None:
    assert "custom" in SKILL_LAYERS
    assert "official" in SKILL_LAYERS


def test_parse_custom_skill_file(tmp_path: Path) -> None:
    _write(tmp_path / "skills" / "custom" / "my-custom-tool" / "SKILL.md", SAMPLE_SKILL)

    skill_md = tmp_path / "skills" / "custom" / "my-custom-tool" / "SKILL.md"
    record = parse_skill_file(skill_md, tmp_path)

    assert record is not None
    assert record.id == "skill:my-custom-tool"
    assert record.name == "my-custom-tool"
    assert record.description == "A custom tool for testing"
    assert record.metadata["layer"] == "custom"
    assert "layer:custom" in record.tags


def test_scan_skills_includes_custom_layer(tmp_path: Path) -> None:
    _write(tmp_path / "skills" / "custom" / "tool-a" / "SKILL.md", SAMPLE_SKILL)
    _write(
        tmp_path / "skills" / "shared" / "tool-b" / "SKILL.md",
        "---\nname: tool-b\ndescription: shared tool\n---\nShared tool body.",
    )

    records = scan_skills(tmp_path)
    assert len(records) == 2

    layers = {r.metadata["layer"] for r in records}
    assert "custom" in layers
    assert "shared" in layers


def test_scan_skills_prefers_official_over_external_for_duplicate_ids(tmp_path: Path) -> None:
    _write(
        tmp_path / "skills" / "external" / "existing-fixed-source" / "duplicate-tool" / "SKILL.md",
        "---\nname: duplicate-tool\ndescription: external duplicate\n---\n# External\n",
    )
    _write(
        tmp_path / "skills" / "official" / "skills-sh-official" / "duplicate-tool" / "SKILL.md",
        "---\nname: duplicate-tool\ndescription: official duplicate\n---\n# Official\n",
    )
    _write(
        tmp_path / "skills" / "external" / "existing-fixed-source" / "unique-tool" / "SKILL.md",
        "---\nname: unique-tool\ndescription: external unique\n---\n# Unique\n",
    )

    records = {record.id: record for record in scan_skills(tmp_path)}

    assert records["skill:duplicate-tool"].metadata["layer"] == "official"
    assert records["skill:duplicate-tool"].source_path == "skills/official/skills-sh-official/duplicate-tool/SKILL.md"
    assert records["skill:unique-tool"].metadata["layer"] == "external"
