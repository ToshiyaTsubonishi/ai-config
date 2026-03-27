from __future__ import annotations

import json
from pathlib import Path

import yaml

from ai_config.vendor.skill_vendor import VendorError
from ai_config.vendor.skills_sh_official import (
    extract_skills_sh_official_repo_slugs,
    refresh_skills_sh_official_manifest,
)


def test_extract_skills_sh_official_repo_slugs_deduplicates_repo_entries() -> None:
    html = (
        r"{\"repo\":\"openai/skills\"},{\"repo\":\"anthropics/skills\"},"
        r"{\"repo\":\"openai/skills\"},{\"repo\":\"cloudflare/skills\"}"
    )

    assert extract_skills_sh_official_repo_slugs(html) == [
        "anthropics/skills",
        "cloudflare/skills",
        "openai/skills",
    ]


def test_refresh_skills_sh_official_manifest_writes_manifest_and_skipped_report(tmp_path: Path) -> None:
    html = (
        r"{\"repo\":\"openai/skills\"},{\"repo\":\"pulumi/agent-skills-private\"},"
        r"{\"repo\":\"cloudflare/skills\"}"
    )

    def resolver(repo_slug: str) -> tuple[str, str]:
        if repo_slug == "pulumi/agent-skills-private":
            raise VendorError("Cannot resolve pulumi/agent-skills-private: repository not found")
        return "main", ("a" if repo_slug == "openai/skills" else "b") * 40

    summary = refresh_skills_sh_official_manifest(
        repo_root=tmp_path,
        html=html,
        resolver=resolver,
    )

    manifest = yaml.safe_load((tmp_path / "config" / "skills_sh_official.yaml").read_text(encoding="utf-8"))
    skipped = json.loads((tmp_path / "config" / "skills_sh_official_skipped.json").read_text(encoding="utf-8"))

    assert summary["total_discovered"] == 3
    assert summary["total_public"] == 2
    assert summary["total_skipped"] == 1

    assert set(manifest["sources"]) == {"cloudflare__skills", "openai__skills"}
    assert manifest["sources"]["openai__skills"]["repo_slug"] == "openai/skills"
    assert manifest["sources"]["cloudflare__skills"]["ref"] == "b" * 40

    assert skipped["total_skipped"] == 1
    assert skipped["skipped"][0]["repo_slug"] == "pulumi/agent-skills-private"
