from __future__ import annotations

from pathlib import Path

from ai_config.registry.path_metadata import infer_source_repo_and_domain


def test_infer_external_source_and_domain() -> None:
    source_repo, domain = infer_source_repo_and_domain(
        Path("external/anthropics-knowledge-work-plugins/sales/skills/call-prep/SKILL.md")
    )
    assert source_repo == "anthropics-knowledge-work-plugins"
    assert domain == "sales"


def test_infer_official_source_and_domain() -> None:
    source_repo, domain = infer_source_repo_and_domain(Path("official/openai__skills/skill-creator/SKILL.md"))
    assert source_repo == "openai__skills"
    assert domain == "skill-creator"


def test_infer_custom_domain_from_nested_layout() -> None:
    source_repo, domain = infer_source_repo_and_domain(Path("custom/human_resources/hr-recruitment/SKILL.md"))
    assert source_repo == "local"
    assert domain == "human_resources"


def test_infer_local_flat_layout_fallback() -> None:
    source_repo, domain = infer_source_repo_and_domain(Path("custom/data-normalization-playbook/SKILL.md"))
    assert source_repo == "local"
    assert domain == "custom"
