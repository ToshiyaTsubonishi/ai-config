#!/usr/bin/env python3
"""Render separate-project Cloud Run staging assets for ai-config topology."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
AI_CONFIG_REPO = ROOT.parents[2]
PROVIDER_REPO = AI_CONFIG_REPO.parent / "ai-config-provider"

TEMPLATE_OUTPUTS = {
    "ai-config-selector.service.yaml.tmpl": "ai-config-selector.service.yaml",
    "ai-config-provider.service.yaml.tmpl": "ai-config-provider.service.yaml",
    "ai-config-mcpo.service.yaml.tmpl": "ai-config-mcpo.service.yaml",
    "ai-config-provider-mcpo.service.yaml.tmpl": "ai-config-provider-mcpo.service.yaml",
    "open-webui.service.mcpo.yaml.tmpl": "open-webui.service.mcpo.yaml",
    "open-webui.tool-server-connections.json.tmpl": "open-webui.tool-server-connections.json",
}

PLACEHOLDER_RE = re.compile(r"{{([A-Z0-9_]+)}}")


def _load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def _require_mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"'{key}' must be a mapping")
    return value


def _optional_mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"'{key}' must be a mapping")
    return value


def _optional_list(parent: dict[str, Any], key: str) -> list[Any]:
    value = parent.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"'{key}' must be a list")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' must be a non-empty string")
    return value.strip()


def _require_scalar_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if value is None:
        raise ValueError(f"'{key}' must be a non-empty scalar")
    if isinstance(value, (int, float)):
        text = str(value)
    elif isinstance(value, str):
        text = value.strip()
    else:
        raise ValueError(f"'{key}' must be a non-empty scalar")

    if not text:
        raise ValueError(f"'{key}' must be a non-empty scalar")
    return text


def _service_url(service_name: str, project_number: str, region: str) -> str:
    return f"https://{service_name}-{project_number}.{region}.run.app"


def _git_head(repo_dir: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()
        return value or None
    except Exception:
        return None


def _provider_bundle_metadata(provider_repo: Path) -> dict[str, Any]:
    metadata_path = provider_repo / "provider-bundle" / ".index" / "provider-bundle-metadata.json"
    if not metadata_path.exists():
        return {}
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _render_template(text: str, values: dict[str, str]) -> str:
    rendered = text
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    unresolved = sorted(set(match.group(1) for match in PLACEHOLDER_RE.finditer(rendered)))
    if unresolved:
        raise ValueError(f"unresolved placeholders in template: {', '.join(unresolved)}")
    return rendered


def _build_values(config: dict[str, Any], mcpo_api_key: str | None) -> dict[str, str]:
    project_id = _require_string(config, "project_id")
    project_number = _require_scalar_string(config, "project_number")
    region = _require_string(config, "region")
    service_account = _require_string(config, "service_account")
    cloudsql_instance = _require_string(config, "cloudsql_instance")
    google_oauth_scope = str(config.get("google_oauth_scope") or "openid email profile").strip()

    if not project_number.isdigit():
        raise ValueError("'project_number' must be numeric")
    if not google_oauth_scope:
        raise ValueError("'google_oauth_scope' must be a non-empty string when provided")

    images = _require_mapping(config, "images")
    buckets = _require_mapping(config, "buckets")
    secrets = _require_mapping(config, "secrets")
    tool_server = _require_mapping(config, "tool_server_connections")
    provenance = _optional_mapping(config, "provenance")
    openai = _optional_mapping(config, "openai")
    bundle_metadata = _provider_bundle_metadata(PROVIDER_REPO)

    selector_url = _service_url("ai-config-selector", project_number, region)
    provider_url = _service_url("ai-config-provider", project_number, region)
    selector_mcpo_url = _service_url("ai-config-mcpo", project_number, region)
    provider_mcpo_url = _service_url("ai-config-provider-mcpo", project_number, region)
    open_webui_url = _service_url("open-webui", project_number, region)

    selector_commit_sha = (
        str(provenance.get("selector_commit_sha") or "").strip()
        or _git_head(AI_CONFIG_REPO)
        or "unknown"
    )
    provider_commit_sha = (
        str(provenance.get("provider_commit_sha") or "").strip()
        or _git_head(PROVIDER_REPO)
        or "unknown"
    )
    provider_bundle_version = (
        str(provenance.get("provider_bundle_version") or "").strip()
        or str(bundle_metadata.get("bundle_version") or "").strip()
        or "unknown"
    )
    provider_bundle_source_commit_sha = (
        str(provenance.get("provider_bundle_source_commit_sha") or "").strip()
        or str(bundle_metadata.get("source_ai_config_commit_sha") or "").strip()
        or selector_commit_sha
    )

    openai_enable = bool(openai.get("enable", False))
    openai_api_base_urls = _optional_list(openai, "api_base_urls")
    openai_api_keys_secret = (
        str(openai.get("api_keys_secret") or "").strip()
        or _require_string(secrets, "gemini_api_key")
    )
    openai_api_configs = openai.get("api_configs", {})
    if openai_enable:
        if not openai_api_base_urls:
            raise ValueError("'openai.api_base_urls' must be a non-empty list when openai.enable is true")
        if not openai_api_keys_secret:
            raise ValueError("'openai.api_keys_secret' must be a non-empty string when openai.enable is true")
        if not isinstance(openai_api_configs, dict):
            raise ValueError("'openai.api_configs' must be a mapping when openai.enable is true")
    else:
        openai_api_configs = {}

    return {
        "PROJECT_ID": project_id,
        "PROJECT_NUMBER": project_number,
        "REGION": region,
        "SERVICE_ACCOUNT": service_account,
        "CLOUDSQL_INSTANCE": cloudsql_instance,
        "CLOUDSQL_CONNECTION": f"{project_id}:{region}:{cloudsql_instance}",
        "SELECTOR_IMAGE": _require_string(images, "selector"),
        "PROVIDER_IMAGE": _require_string(images, "provider"),
        "OPEN_WEBUI_IMAGE": _require_string(images, "open_webui"),
        "OPEN_TERMINAL_IMAGE": _require_string(images, "open_terminal"),
        "SEARXNG_IMAGE": _require_string(images, "searxng"),
        "MCPO_IMAGE": _require_string(images, "mcpo"),
        "WEBUI_BUCKET": _require_string(buckets, "open_webui"),
        "SEARXNG_BUCKET": _require_string(buckets, "searxng"),
        "MCPO_API_KEY_SECRET": _require_string(secrets, "mcpo_api_key"),
        "OPENWEBUI_TOOL_SERVER_CONNECTIONS_SECRET": _require_string(secrets, "tool_server_connections"),
        "WEBUI_SECRET_KEY_SECRET": _require_string(secrets, "webui_secret_key"),
        "GEMINI_API_KEY_SECRET": _require_string(secrets, "gemini_api_key"),
        "GOOGLE_CLIENT_ID_SECRET": _require_string(secrets, "google_client_id"),
        "GOOGLE_CLIENT_SECRET_SECRET": _require_string(secrets, "google_client_secret"),
        "DATABASE_URL_SECRET": _require_string(secrets, "database_url"),
        "OPEN_TERMINAL_API_KEY_SECRET": _require_string(secrets, "open_terminal_api_key"),
        "SEARXNG_SECRET_SECRET": _require_string(secrets, "searxng_secret"),
        "AI_CONFIG_SELECTOR_URL": selector_url,
        "AI_CONFIG_SELECTOR_MCP_URL": f"{selector_url}/mcp",
        "AI_CONFIG_PROVIDER_URL": provider_url,
        "AI_CONFIG_PROVIDER_MCP_URL": f"{provider_url}/mcp",
        "AI_CONFIG_MCPO_URL": selector_mcpo_url,
        "AI_CONFIG_PROVIDER_MCPO_URL": provider_mcpo_url,
        "OPEN_WEBUI_URL": open_webui_url,
        "GOOGLE_REDIRECT_URI": f"{open_webui_url}/oauth/google/callback",
        "GOOGLE_OAUTH_SCOPE": google_oauth_scope,
        "OPENAI_ENABLE": "True" if openai_enable else "False",
        "OPENAI_API_BASE_URLS": ";".join(str(url).strip() for url in openai_api_base_urls),
        "OPENAI_API_KEYS_SECRET": openai_api_keys_secret,
        "OPENAI_API_CONFIGS_JSON": json.dumps(openai_api_configs, separators=(",", ":"), ensure_ascii=False),
        "MCPO_API_KEY_VALUE": mcpo_api_key or _require_string(tool_server, "mcpo_api_key_placeholder"),
        "SELECTOR_COMMIT_SHA": selector_commit_sha,
        "PROVIDER_COMMIT_SHA": provider_commit_sha,
        "PROVIDER_BUNDLE_VERSION": provider_bundle_version,
        "PROVIDER_BUNDLE_SOURCE_COMMIT_SHA": provider_bundle_source_commit_sha,
    }


def _write_outputs(output_dir: Path, values: dict[str, str]) -> list[str]:
    written: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for template_name, output_name in TEMPLATE_OUTPUTS.items():
        template_path = TEMPLATE_DIR / template_name
        text = template_path.read_text(encoding="utf-8")
        rendered = _render_template(text, values)
        output_path = output_dir / output_name
        output_path.write_text(rendered + ("" if rendered.endswith("\n") else "\n"), encoding="utf-8")
        written.append(output_name)

    metadata = {
        "project_id": values["PROJECT_ID"],
        "project_number": values["PROJECT_NUMBER"],
        "region": values["REGION"],
        "service_account": values["SERVICE_ACCOUNT"],
        "cloudsql_connection": values["CLOUDSQL_CONNECTION"],
        "provenance": {
            "selector_commit_sha": values["SELECTOR_COMMIT_SHA"],
            "provider_commit_sha": values["PROVIDER_COMMIT_SHA"],
            "provider_bundle_version": values["PROVIDER_BUNDLE_VERSION"],
            "provider_bundle_source_commit_sha": values["PROVIDER_BUNDLE_SOURCE_COMMIT_SHA"],
        },
        "urls": {
            "selector": values["AI_CONFIG_SELECTOR_URL"],
            "selector_mcp": values["AI_CONFIG_SELECTOR_MCP_URL"],
            "provider": values["AI_CONFIG_PROVIDER_URL"],
            "provider_mcp": values["AI_CONFIG_PROVIDER_MCP_URL"],
            "selector_mcpo": values["AI_CONFIG_MCPO_URL"],
            "provider_mcpo": values["AI_CONFIG_PROVIDER_MCPO_URL"],
            "open_webui": values["OPEN_WEBUI_URL"],
            "google_redirect_uri": values["GOOGLE_REDIRECT_URI"],
        },
        "files": written,
    }
    metadata_path = output_dir / "stack-metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written.append(metadata_path.name)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Cloud Run staging stack assets")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "stack.example.yaml",
        help="Path to the staging value file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "rendered",
        help="Directory to write rendered manifests and JSON",
    )
    parser.add_argument(
        "--mcpo-api-key",
        default=None,
        help="Optional concrete MCPO API key to inject into tool-server JSON",
    )
    args = parser.parse_args(argv)

    try:
        config = _load_config(args.config)
        values = _build_values(config, args.mcpo_api_key)
        written = _write_outputs(args.output_dir, values)
    except Exception as error:  # pragma: no cover - exercised via subprocess tests
        print(f"render_stack.py: {error}", file=sys.stderr)
        return 1

    print(json.dumps({"output_dir": str(args.output_dir), "files": written}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
