from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = REPO_ROOT / "deploy" / "cloudrun" / "release"
SCRIPT_PATH = RELEASE_DIR / "publish_ghcr_release.py"


def _load_release_module():
    spec = importlib.util.spec_from_file_location("publish_ghcr_release", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_manifest_uses_digest_refs_and_provenance() -> None:
    release = _load_release_module()

    manifest = release.build_release_manifest(
        github_owner="tsytbns",
        generated_at="2026-04-15T00:00:00Z",
        selector=release.ImageRelease(
            repository="ghcr.io/tsytbns/ai-config-selector-serving",
            tag="selector-abc123def456",
            digest="sha256:" + "1" * 64,
            source_commit_sha="abc123def4567890",
            source_repository="https://github.com/tsytbns/ai-config",
        ),
        provider=release.ImageRelease(
            repository="ghcr.io/tsytbns/ai-config-provider",
            tag="provider-fedcba654321-bundle-v1",
            digest="sha256:" + "2" * 64,
            source_commit_sha="fedcba6543210987",
            source_repository="https://github.com/tsytbns/ai-config-provider",
            bundle_version="bundle-v1",
            bundle_source_commit_sha="abc123def4567890",
        ),
    )

    assert manifest["selector"]["image_ref"] == (
        "ghcr.io/tsytbns/ai-config-selector-serving@sha256:" + "1" * 64
    )
    assert manifest["provider"]["image_ref"] == (
        "ghcr.io/tsytbns/ai-config-provider@sha256:" + "2" * 64
    )
    assert manifest["provider"]["bundle_version"] == "bundle-v1"
    assert manifest["cloudrun"]["images"]["selector"] == manifest["selector"]["image_ref"]
    assert manifest["cloudrun"]["provenance"]["provider_bundle_source_commit_sha"] == "abc123def4567890"
    assert manifest["distribution"]["temporary_public_required_for_constrained_production"] is True


def test_release_helpers_cover_default_tags_and_buildx_digest_formats() -> None:
    release = _load_release_module()

    assert release.default_selector_tag("0fa50eb0b1ea05547ef6c9edaa534382ce7ff1a2") == "selector-0fa50eb0b1ea"
    assert release.default_provider_tag(
        "94f329dec68dfa02ff2323c1164ca68431942b49",
        "0fa50eb0b1ea-7c12f6aae5b8",
    ).startswith("provider-94f329dec68d-0fa50eb0b1ea-7c12f6aae5b8")

    assert release.extract_buildx_digest(
        {"containerimage.digest": "sha256:" + "3" * 64}
    ) == "sha256:" + "3" * 64
    assert release.extract_buildx_digest(
        {"containerimage.descriptor": {"digest": "sha256:" + "4" * 64}}
    ) == "sha256:" + "4" * 64


def test_release_docs_and_workflow_cover_constrained_production_path() -> None:
    cloudrun_readme = (REPO_ROOT / "deploy" / "cloudrun" / "README.md").read_text(encoding="utf-8")
    release_readme = (RELEASE_DIR / "README.md").read_text(encoding="utf-8")
    staging_readme = (REPO_ROOT / "deploy" / "cloudrun" / "staging" / "README.md").read_text(
        encoding="utf-8"
    )
    guide = (REPO_ROOT / "deploy" / "cloudrun" / "gcp-gui-setup-guide.ja.md").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github" / "workflows" / "publish-ghcr-release.yml").read_text(
        encoding="utf-8"
    )

    for expected in [
        "Constrained Production Release",
        "release/publish_ghcr_release.py",
        "release/README.md",
        "publish-ghcr-release.yml",
        "ghcr-release-manifest.json",
        "GitHub Packages",
        "@sha256:",
    ]:
        assert expected in cloudrun_readme

    for expected in [
        "publish_ghcr_release.py",
        "ghcr-release-manifest.json",
        "provider-bundle-metadata.json",
        "temporary_public_required_for_constrained_production",
        "Cloud Run",
    ]:
        assert expected in release_readme

    for expected in [
        "ghcr-release-manifest.json",
        "cloudrun.images.selector",
        "cloudrun.provenance",
        "@sha256:",
    ]:
        assert expected in staging_readme

    for expected in [
        "publish_ghcr_release.py",
        "ghcr-release-manifest.json",
        "GitHub Packages",
        "@sha256:",
        "public",
    ]:
        assert expected in guide

    for expected in [
        "Publish GHCR Release",
        "docker/login-action@v3",
        "AI_CONFIG_PROVIDER_REPO_TOKEN",
        "publish_ghcr_release.py",
        "ghcr-release-manifest.json",
    ]:
        assert expected in workflow
