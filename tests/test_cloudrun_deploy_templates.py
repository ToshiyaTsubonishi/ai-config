from __future__ import annotations

import json
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
    assert container["image"].endswith("/ai-config-selector-serving:main")
    assert container["ports"] == [{"name": "http1", "containerPort": 8080}]
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
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
        "ai-config-selector.service.yaml",
        "ai-config-mcpo.service.yaml",
        "open-webui.service.mcpo.yaml",
        "open-webui.tool-server-connections.example.json",
        "MCPO_API_KEY",
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS",
        "ENABLE_PERSISTENT_CONFIG=False",
        "ENABLE_LOGIN_FORM=False",
        "/openapi.json",
    ]:
        assert expected in text
