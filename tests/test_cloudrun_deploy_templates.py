from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = REPO_ROOT / "deploy" / "cloudrun"


def _load_yaml(name: str) -> dict:
    return yaml.safe_load((DEPLOY_DIR / name).read_text(encoding="utf-8"))


def _container_env(container: dict) -> dict[str, dict]:
    return {item["name"]: item for item in container.get("env", [])}


def test_ai_config_selector_service_template() -> None:
    service = _load_yaml("ai-config-selector.service.yaml")

    assert service["apiVersion"] == "serving.knative.dev/v1"
    assert service["kind"] == "Service"
    assert service["metadata"]["name"] == "ai-config-selector"
    assert "status" not in service
    assert service["metadata"]["annotations"]["run.googleapis.com/ingress"] == "all"
    assert service["metadata"]["annotations"]["run.googleapis.com/invoker-iam-disabled"] == "true"

    container = service["spec"]["template"]["spec"]["containers"][0]
    assert container["name"] == "ai-config-selector-1"
    assert (
        container["image"]
        == "ghcr.io/tsytbns/ai-config-selector-serving@sha256:bd606a4de2c81e98fb99c5217b5e5a83fee817a1b856583b4017c0980c463eb8"
    )
    assert container["ports"] == [{"name": "http1", "containerPort": 8080}]
    assert container["livenessProbe"]["httpGet"]["path"] == "/livez"
    assert container["startupProbe"]["tcpSocket"]["port"] == 8080
    assert container.get("env", []) == []


def test_ai_config_mcpo_service_template() -> None:
    service = _load_yaml("ai-config-mcpo.service.yaml")

    assert service["metadata"]["name"] == "ai-config-mcpo"
    assert service["metadata"]["annotations"]["run.googleapis.com/ingress"] == "all"

    container = service["spec"]["template"]["spec"]["containers"][0]
    assert container["name"] == "ai-config-mcpo-1"
    assert container["image"] == "ghcr.io/open-webui/mcpo:v0.0.20"
    assert container["command"] == ["/bin/sh"]

    command = container["args"][1]
    assert "mcpo" in command
    assert "--host 0.0.0.0" in command
    assert "--strict-auth" in command
    assert "--server-type \"streamable-http\"" in command
    assert "\"${PORT:-8080}\"" in command
    assert "\"$MCPO_API_KEY\"" in command
    assert "\"$AI_CONFIG_SELECTOR_MCP_URL\"" in command

    env = _container_env(container)
    assert env["AI_CONFIG_SELECTOR_MCP_URL"]["value"] == (
        "https://ai-config-selector-424287527578.asia-northeast1.run.app/mcp"
    )
    assert env["MCPO_API_KEY"]["valueFrom"]["secretKeyRef"]["name"] == "MCPO_API_KEY"
    assert container["livenessProbe"]["tcpSocket"]["port"] == 8080
    assert container["startupProbe"]["tcpSocket"]["port"] == 8080


def test_open_webui_service_template_includes_mcpo_connection() -> None:
    service = _load_yaml("open-webui.service.mcpo.yaml")

    assert service["metadata"]["name"] == "open-webui"
    assert "status" not in service
    assert service["spec"]["template"]["spec"]["serviceAccountName"] == (
        "open-webui-runner@sbi-art-auction.iam.gserviceaccount.com"
    )

    containers = {
        container["name"]: container for container in service["spec"]["template"]["spec"]["containers"]
    }
    assert set(containers) == {"open-webui-1", "open-terminal-1", "searxng-1"}

    webui_env = _container_env(containers["open-webui-1"])
    assert webui_env["ENABLE_PERSISTENT_CONFIG"]["value"] == "False"
    assert webui_env["ENABLE_OAUTH_PERSISTENT_CONFIG"]["value"] == "False"
    assert webui_env["ENABLE_LOGIN_FORM"]["value"] == "False"
    assert webui_env["ENABLE_DIRECT_CONNECTIONS"]["value"] == "True"
    assert webui_env["TOOL_SERVER_CONNECTIONS"]["valueFrom"]["secretKeyRef"]["name"] == (
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS"
    )
    assert webui_env["WEBUI_SECRET_KEY"]["valueFrom"]["secretKeyRef"]["name"] == "WEBUI_SECRET_KEY"


def test_open_webui_tool_server_connections_secret_example() -> None:
    payload = json.loads(
        (DEPLOY_DIR / "open-webui.tool-server-connections.example.json").read_text(encoding="utf-8")
    )

    assert payload == [
        {
            "type": "openapi",
            "url": "https://ai-config-mcpo-424287527578.asia-northeast1.run.app",
            "spec_type": "url",
            "spec": "",
            "path": "openapi.json",
            "auth_type": "bearer",
            "key": "__REPLACE_WITH_MCPO_API_KEY__",
            "config": {"enable": True},
            "info": {
                "id": "ai-config-mcpo",
                "name": "ai-config (MCPO)",
                "description": "ai-config selector tools exposed through MCPO on Cloud Run",
            },
        }
    ]


def test_cloudrun_readme_covers_mcpo_topology() -> None:
    text = (DEPLOY_DIR / "README.md").read_text(encoding="utf-8")

    for expected in [
        "gcp-gui-setup-guide.ja.md",
        "cloudbuild.selector.yaml",
        "render_selector_service.py",
        "ai-config-selector.service.yaml",
        "ai-config-mcpo.service.yaml",
        "open-webui.service.mcpo.yaml",
        "open-webui.tool-server-connections.example.json",
        "MCPO_API_KEY",
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS",
        "ENABLE_PERSISTENT_CONFIG=False",
        "ENABLE_LOGIN_FORM=False",
        "/livez",
        "/openapi.json",
        "--config deploy/cloudrun/cloudbuild.selector.yaml",
    ]:
        assert expected in text


def test_cloudrun_readme_avoids_invalid_gcloud_build_flag() -> None:
    text = (DEPLOY_DIR / "README.md").read_text(encoding="utf-8")

    assert "gcloud builds submit \\\n  --tag" not in text
    assert "gcloud builds submit \\\n  --project \"$PROJECT_ID\" \\\n  --config deploy/cloudrun/cloudbuild.selector.yaml" in text


def test_gcp_gui_setup_guide_covers_console_flow() -> None:
    text = (DEPLOY_DIR / "gcp-gui-setup-guide.ja.md").read_text(encoding="utf-8")

    for expected in [
        "Cloud Run",
        "Secret Manager",
        "MCPO_API_KEY",
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS",
        "Secret Manager Secret Accessor",
        "ai-config-selector",
        "ai-config-mcpo",
        "open-webui",
        "ENABLE_PERSISTENT_CONFIG",
        "ENABLE_LOGIN_FORM",
        "Open WebUI",
        "/livez",
        "＋",
    ]:
        assert expected in text


def test_gcp_gui_setup_guide_handles_no_github_no_gcloud_constraints() -> None:
    text = (DEPLOY_DIR / "gcp-gui-setup-guide.ja.md").read_text(encoding="utf-8")

    for expected in [
        "GitHub を GCP に接続しない",
        "`gcloud` は使いません",
        "事前にコンテナイメージ",
        "GHCR",
        "Docker Hub",
        "社内レジストリ",
        "docker build -f deploy/cloudrun/Dockerfile",
        "gh auth status",
        "gh api user --jq '.login'",
        "write:packages",
        "docker-credential-desktop",
        "docker --config /tmp/docker-ghcr",
        "artifactregistry.repositories.uploadArtifacts",
    ]:
        assert expected in text


def test_cloudbuild_selector_config_uses_deploy_dockerfile() -> None:
    payload = _load_yaml("cloudbuild.selector.yaml")

    step = payload["steps"][0]
    assert step["name"] == "gcr.io/cloud-builders/docker"
    assert step["args"] == ["build", "-f", "deploy/cloudrun/Dockerfile", "-t", "${_IMAGE}", "."]
    assert payload["images"] == ["${_IMAGE}"]


def test_render_selector_service_script(tmp_path: Path) -> None:
    output_path = tmp_path / "selector.yaml"

    subprocess.run(
        [
            sys.executable,
            str(DEPLOY_DIR / "render_selector_service.py"),
            "--project-id",
            "abiding-aspect-457603-m8",
            "--project-number",
            "546079316858",
            "--region",
            "asia-northeast1",
            "--image",
            "asia-northeast1-docker.pkg.dev/abiding-aspect-457603-m8/cloud-run-source-deploy/ai-config-selector-serving:test",
            "--service-name",
            "ai-config-selector-test",
            "--output",
            str(output_path),
        ],
        check=True,
    )

    rendered = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    container = rendered["spec"]["template"]["spec"]["containers"][0]

    assert rendered["metadata"]["name"] == "ai-config-selector-test"
    assert rendered["metadata"]["namespace"] == "546079316858"
    assert rendered["metadata"]["labels"]["cloud.googleapis.com/location"] == "asia-northeast1"
    assert container["name"] == "ai-config-selector-test-1"
    assert container["image"].endswith("/ai-config-selector-serving:test")
    assert "serviceAccountName" not in rendered["spec"]["template"]["spec"]


def test_selector_dockerfile_installs_rust_toolchain_for_sudachipy() -> None:
    text = (DEPLOY_DIR / "Dockerfile").read_text(encoding="utf-8")

    for expected in ["build-essential", "cargo", "rustc"]:
        assert expected in text
