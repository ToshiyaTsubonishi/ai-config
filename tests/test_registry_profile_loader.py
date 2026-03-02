from __future__ import annotations

from pathlib import Path

from ai_config.registry.models import ToolRecord
from ai_config.registry.profile_loader import filter_records_by_profile, load_profiles


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sample_records() -> list[ToolRecord]:
    return [
        ToolRecord(
            id="skill:anthropic",
            name="anthropic-skill",
            description="anthropic",
            source_path="skills/external/anthropics-skills/skills/docx/SKILL.md",
            tool_kind="skill",
        ),
        ToolRecord(
            id="skill:kwp",
            name="kwp-skill",
            description="kwp",
            source_path="skills/external/anthropics-knowledge-work-plugins/sales/skills/call-prep/SKILL.md",
            tool_kind="skill",
        ),
        ToolRecord(
            id="skill:anti",
            name="anti-skill",
            description="anti",
            source_path="skills/external/antigravity-awesome-skills/skills/test/SKILL.md",
            tool_kind="skill",
        ),
    ]


def test_load_profiles_and_filter_records(tmp_path: Path) -> None:
    _write(
        tmp_path / "config/index_profiles.yaml",
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
    profiles = load_profiles(tmp_path)
    assert "default" in profiles
    assert "full" in profiles

    records = _sample_records()
    default_records = filter_records_by_profile(records, profiles["default"])
    assert len(default_records) == 2
    assert all("antigravity-awesome-skills" not in r.source_path for r in default_records)

    full_records = filter_records_by_profile(records, profiles["full"])
    assert len(full_records) == 3
