from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR = REPO_ROOT / "deploy" / "cloudrun" / "production"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_fixture_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "project_id: sbi-art-auction",
                "project_number: 424287527578",
                "region: asia-northeast1",
                "google_oauth_scope: openid email profile",
                "service_account: open-webui-runner@sbi-art-auction.iam.gserviceaccount.com",
                "cloudsql_instance: open-web-ui",
                "openai:",
                "  enable: true",
                "  api_base_urls:",
                "    - https://generativelanguage.googleapis.com/v1beta/openai",
                "  api_keys_secret: GEMINI_API_KEY",
                "  api_configs:",
                "    \"0\":",
                "      enable: true",
                "      tags: []",
                "      prefix_id: \"\"",
                "      model_ids: []",
                "      connection_type: external",
                "      auth_type: bearer",
                "images:",
                "  selector: ghcr.io/toshiyatsubonishi/ai-config-selector-serving@sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "  provider: ghcr.io/toshiyatsubonishi/ai-config-provider@sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "  open_webui: asia-northeast1-docker.pkg.dev/sbi-art-auction/ghcr/open-webui/open-webui:main",
                "  open_terminal: asia-northeast1-docker.pkg.dev/sbi-art-auction/ghcr/ghcr.io/open-webui/open-terminal:latest",
                "  searxng: asia-northeast1-docker.pkg.dev/sbi-art-auction/ghcr/ghcr.io/searxng/searxng:latest",
                "  mcpo: asia-northeast1-docker.pkg.dev/sbi-art-auction/ghcr/ghcr.io/open-webui/mcpo:latest",
                "buckets:",
                "  open_webui: open-webui-sbiaa",
                "  searxng: searxng-sbiaa",
                "secrets:",
                "  mcpo_api_key: MCPO_API_KEY",
                "  tool_server_connections: OPENWEBUI_TOOL_SERVER_CONNECTIONS",
                "  webui_secret_key: WEBUI_SECRET_KEY",
                "  gemini_api_key: GEMINI_API_KEY",
                "  google_client_id: open_webui_oauth_client_id",
                "  google_client_secret: open_webui_oauth_client_secret",
                "  database_url: DATABASE_URL",
                "  open_terminal_api_key: OPEN_TERMINAL_API_KEY",
                "  searxng_secret: SEARXNG_SECRET",
                "tool_server_connections:",
                "  mcpo_api_key_placeholder: __PLACEHOLDER__",
                "provenance:",
                "  selector_commit_sha: selector-prod-sha",
                "  provider_commit_sha: provider-prod-sha",
                "  provider_bundle_version: prod-bundle-v1",
                "  provider_bundle_source_commit_sha: ai-config-prod-source",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_production_stack_example_targets_sbi_art_auction() -> None:
    config = _load_yaml(PRODUCTION_DIR / "stack.example.yaml")

    assert config["project_id"] == "sbi-art-auction"
    assert str(config["project_number"]) == "424287527578"
    assert config["region"] == "asia-northeast1"
    assert config["service_account"] == "open-webui-runner@sbi-art-auction.iam.gserviceaccount.com"
    assert config["cloudsql_instance"] == "open-web-ui"
    assert config["buckets"]["open_webui"] == "open-webui-sbiaa"
    assert config["buckets"]["searxng"] == "searxng-sbiaa"
    assert config["images"]["selector"].startswith("ghcr.io/toshiyatsubonishi/ai-config-selector-serving@sha256:")
    assert config["images"]["provider"].startswith("ghcr.io/toshiyatsubonishi/ai-config-provider@sha256:")


def test_production_wrapper_renders_prod_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "stack.yaml"
    output_dir = tmp_path / "rendered"
    _write_fixture_config(config_path)

    result = subprocess.run(
        [
            sys.executable,
            str(PRODUCTION_DIR / "render_stack.py"),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--mcpo-api-key",
            "prod-secret",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    metadata = json.loads((output_dir / "stack-metadata.json").read_text(encoding="utf-8"))
    assert metadata["project_id"] == "sbi-art-auction"
    assert metadata["project_number"] == "424287527578"
    assert metadata["urls"]["selector"] == "https://ai-config-selector-424287527578.asia-northeast1.run.app"
    assert metadata["provenance"]["provider_bundle_version"] == "prod-bundle-v1"

    selector = _load_yaml(output_dir / "ai-config-selector.service.yaml")
    provider = _load_yaml(output_dir / "ai-config-provider.service.yaml")
    open_webui = _load_yaml(output_dir / "open-webui.service.mcpo.yaml")

    assert selector["metadata"]["namespace"] == "424287527578"
    selector_container = selector["spec"]["template"]["spec"]["containers"][0]
    assert selector_container["image"] == (
        "ghcr.io/toshiyatsubonishi/ai-config-selector-serving@sha256:"
        "1111111111111111111111111111111111111111111111111111111111111111"
    )

    provider_container = provider["spec"]["template"]["spec"]["containers"][0]
    provider_env = {item["name"]: item for item in provider_container["env"]}
    assert provider_container["image"] == (
        "ghcr.io/toshiyatsubonishi/ai-config-provider@sha256:"
        "2222222222222222222222222222222222222222222222222222222222222222"
    )
    assert provider_env["AI_CONFIG_SELECTOR_BASE_URL"]["value"] == (
        "https://ai-config-selector-424287527578.asia-northeast1.run.app"
    )

    webui_env = {
        item["name"]: item
        for item in open_webui["spec"]["template"]["spec"]["containers"][0]["env"]
    }
    assert webui_env["GCS_BUCKET_NAME"]["value"] == "open-webui-sbiaa"
    assert webui_env["GOOGLE_OAUTH_SCOPE"]["value"] == "openid email profile"

    tool_connections = json.loads(
        (output_dir / "open-webui.tool-server-connections.json").read_text(encoding="utf-8")
    )
    assert {entry["key"] for entry in tool_connections} == {"prod-secret"}
    assert tool_connections[0]["url"] == "https://ai-config-mcpo-424287527578.asia-northeast1.run.app"
    assert tool_connections[1]["url"] == "https://ai-config-provider-mcpo-424287527578.asia-northeast1.run.app"


def test_production_docs_cover_release_manifest_and_apply_wrapper() -> None:
    readme = (PRODUCTION_DIR / "README.md").read_text(encoding="utf-8")
    root_readme = (REPO_ROOT / "deploy" / "cloudrun" / "README.md").read_text(encoding="utf-8")

    for expected in [
        "sbi-art-auction",
        "ghcr-release-manifest.json",
        "render_stack.py",
        "apply_rendered_stack.sh",
        "ENABLE_PERSISTENT_CONFIG=False",
        "GHCR",
    ]:
        assert expected in readme

    for expected in [
        "Production Project Assets",
        "production/stack.example.yaml",
        "production/render_stack.py",
        "production/apply_rendered_stack.sh",
    ]:
        assert expected in root_readme
