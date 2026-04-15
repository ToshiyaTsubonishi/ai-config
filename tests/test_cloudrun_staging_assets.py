from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = REPO_ROOT / "deploy" / "cloudrun" / "staging"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_fixture_config(path: Path, *, project_number: str) -> None:
    path.write_text(
        "\n".join(
            [
                "project_id: abiding-aspect-457603-m8",
                f"project_number: {project_number}",
                "region: asia-northeast1",
                "google_oauth_scope: openid email",
                "service_account: open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com",
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
                "  selector: example.com/selector:staging",
                "  provider: example.com/provider:staging",
                "  open_webui: example.com/open-webui:main",
                "  open_terminal: example.com/open-terminal:latest",
                "  searxng: example.com/searxng:latest",
                "  mcpo: ghcr.io/open-webui/mcpo:v0.0.20",
                "buckets:",
                "  open_webui: open-webui-abiding-aspect-457603-m8",
                "  searxng: searxng-abiding-aspect-457603-m8",
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
                "  selector_commit_sha: selector-sha",
                "  provider_commit_sha: provider-sha",
                "  provider_bundle_version: bundle-v1",
                "  provider_bundle_source_commit_sha: ai-config-source-sha",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_staging_example_targets_separate_project() -> None:
    config = _load_yaml(STAGING_DIR / "stack.example.yaml")

    assert config["project_id"] == "abiding-aspect-457603-m8"
    assert config["region"] == "asia-northeast1"
    assert config["google_oauth_scope"] == "openid email"
    assert config["service_account"] == "open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com"
    assert config["cloudsql_instance"] == "open-web-ui"
    assert config["openai"]["enable"] is True
    assert config["openai"]["api_base_urls"] == ["https://generativelanguage.googleapis.com/v1beta/openai"]
    assert config["openai"]["api_keys_secret"] == "GEMINI_API_KEY"
    assert config["buckets"]["open_webui"] == "open-webui-abiding-aspect-457603-m8"
    assert config["buckets"]["searxng"] == "searxng-abiding-aspect-457603-m8"
    assert config["secrets"]["tool_server_connections"] == "OPENWEBUI_TOOL_SERVER_CONNECTIONS"


def test_render_stack_outputs_separate_project_manifests(tmp_path: Path) -> None:
    config_path = tmp_path / "stack.yaml"
    output_dir = tmp_path / "rendered"
    _write_fixture_config(config_path, project_number="123456789012")

    result = subprocess.run(
        [
            sys.executable,
            str(STAGING_DIR / "render_stack.py"),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--mcpo-api-key",
            "staging-secret",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["output_dir"] == str(output_dir)

    metadata = json.loads((output_dir / "stack-metadata.json").read_text(encoding="utf-8"))
    assert metadata["project_id"] == "abiding-aspect-457603-m8"
    assert metadata["project_number"] == "123456789012"
    assert metadata["provenance"] == {
        "selector_commit_sha": "selector-sha",
        "provider_commit_sha": "provider-sha",
        "provider_bundle_version": "bundle-v1",
        "provider_bundle_source_commit_sha": "ai-config-source-sha",
    }
    assert metadata["urls"]["selector"] == "https://ai-config-selector-123456789012.asia-northeast1.run.app"
    assert metadata["urls"]["provider_mcp"] == "https://ai-config-provider-123456789012.asia-northeast1.run.app/mcp"
    assert metadata["urls"]["open_webui"] == "https://open-webui-123456789012.asia-northeast1.run.app"

    selector = _load_yaml(output_dir / "ai-config-selector.service.yaml")
    provider = _load_yaml(output_dir / "ai-config-provider.service.yaml")
    open_webui = _load_yaml(output_dir / "open-webui.service.mcpo.yaml")
    selector_mcpo = _load_yaml(output_dir / "ai-config-mcpo.service.yaml")

    assert selector["metadata"]["namespace"] == "123456789012"
    assert selector["spec"]["template"]["spec"]["serviceAccountName"] == (
        "open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com"
    )
    selector_container = selector["spec"]["template"]["spec"]["containers"][0]
    selector_env = {item["name"]: item for item in selector_container["env"]}
    assert selector["spec"]["template"]["metadata"]["annotations"]["ai-config.dev/commit-sha"] == "selector-sha"
    assert selector_env["AI_CONFIG_DEPLOY_COMMIT_SHA"]["value"] == "selector-sha"
    assert selector_env["AI_CONFIG_DEPLOY_IMAGE"]["value"] == "example.com/selector:staging"
    assert provider["spec"]["template"]["spec"]["containers"][0]["env"][1]["value"] == (
        "https://ai-config-selector-123456789012.asia-northeast1.run.app"
    )
    provider_container = provider["spec"]["template"]["spec"]["containers"][0]
    provider_env = {item["name"]: item for item in provider_container["env"]}
    assert provider["spec"]["template"]["metadata"]["annotations"]["ai-config.dev/provider-bundle-version"] == "bundle-v1"
    assert provider_env["AI_CONFIG_DEPLOY_COMMIT_SHA"]["value"] == "provider-sha"
    assert provider_env["AI_CONFIG_PROVIDER_BUNDLE_VERSION"]["value"] == "bundle-v1"
    assert selector_mcpo["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] == (
        "https://ai-config-selector-123456789012.asia-northeast1.run.app/mcp"
    )

    webui_env = {
        item["name"]: item
        for item in open_webui["spec"]["template"]["spec"]["containers"][0]["env"]
    }
    assert webui_env["WEBUI_URL"]["value"] == "https://open-webui-123456789012.asia-northeast1.run.app"
    assert webui_env["GOOGLE_OAUTH_SCOPE"]["value"] == "openid email"
    assert webui_env["ENABLE_OPENAI_API"]["value"] == "True"
    assert webui_env["OPENAI_API_BASE_URLS"]["value"] == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert webui_env["OPENAI_API_KEYS"]["valueFrom"]["secretKeyRef"]["name"] == "GEMINI_API_KEY"
    assert webui_env["OPENAI_API_CONFIGS"]["value"] == (
        '{"0":{"enable":true,"tags":[],"prefix_id":"","model_ids":[],"connection_type":"external","auth_type":"bearer"}}'
    )
    assert webui_env["GCS_BUCKET_NAME"]["value"] == "open-webui-abiding-aspect-457603-m8"
    assert webui_env["TOOL_SERVER_CONNECTIONS"]["valueFrom"]["secretKeyRef"]["name"] == (
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS"
    )

    tool_connections = json.loads(
        (output_dir / "open-webui.tool-server-connections.json").read_text(encoding="utf-8")
    )
    assert len(tool_connections) == 2
    assert tool_connections[0]["url"] == "https://ai-config-mcpo-123456789012.asia-northeast1.run.app"
    assert tool_connections[1]["url"] == "https://ai-config-provider-mcpo-123456789012.asia-northeast1.run.app"
    assert {entry["key"] for entry in tool_connections} == {"staging-secret"}


def test_render_stack_requires_numeric_project_number(tmp_path: Path) -> None:
    config_path = tmp_path / "stack.yaml"
    output_dir = tmp_path / "rendered"
    _write_fixture_config(config_path, project_number="REPLACE_WITH_PROJECT_NUMBER")

    result = subprocess.run(
        [
            sys.executable,
            str(STAGING_DIR / "render_stack.py"),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "project_number" in result.stderr


def test_render_stack_auto_detects_local_provenance(tmp_path: Path) -> None:
    config_path = tmp_path / "stack.yaml"
    output_dir = tmp_path / "rendered"
    _write_fixture_config(config_path, project_number="123456789012")

    config = config_path.read_text(encoding="utf-8").replace(
        "\nprovenance:\n  selector_commit_sha: selector-sha\n  provider_commit_sha: provider-sha\n  provider_bundle_version: bundle-v1\n  provider_bundle_source_commit_sha: ai-config-source-sha\n",
        "\n",
    )
    config_path.write_text(config, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(STAGING_DIR / "render_stack.py"),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--mcpo-api-key",
            "staging-secret",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    metadata = json.loads((output_dir / "stack-metadata.json").read_text(encoding="utf-8"))
    assert metadata["provenance"]["selector_commit_sha"] != "unknown"
    assert metadata["provenance"]["provider_commit_sha"] != "unknown"


def test_staging_docs_cover_separate_project_flow() -> None:
    readme = (STAGING_DIR / "README.md").read_text(encoding="utf-8")
    guide = (STAGING_DIR / "gcp-gui-setup-guide.ja.md").read_text(encoding="utf-8")
    root_readme = (REPO_ROOT / "deploy" / "cloudrun" / "README.md").read_text(encoding="utf-8")

    for expected in [
        "abiding-aspect-457603-m8",
        "open-webui-abiding-aspect-457603-m8",
        "searxng-abiding-aspect-457603-m8",
        "render_stack.py",
        "apply_rendered_stack.sh",
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS",
        "ai-config-provider-mcpo",
        "stack-metadata.json",
        "commit SHA",
        "provider-bundle version",
    ]:
        assert expected in readme

    for expected in [
        "abiding-aspect-457603-m8",
        "project number",
        "Open WebUI",
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS",
        "ai-config-provider-mcpo",
        "remote-wrapper-contract.md",
    ]:
        assert expected in guide

    for expected in [
        "Separate-Project Staging",
        "staging/stack.example.yaml",
        "staging/render_stack.py",
        "staging/gcp-gui-setup-guide.ja.md",
    ]:
        assert expected in root_readme
