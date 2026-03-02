"""Parser for external catalog-only MCP definitions (.mcp.json)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ai_config.registry.models import ToolRecord

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _plugin_metadata(plugin_root: Path) -> dict[str, Any]:
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.is_file():
        return {}
    return _load_json(plugin_json)


def _description_for(server_name: str, plugin_meta: dict[str, Any], plugin_path: str) -> str:
    plugin_desc = str(plugin_meta.get("description") or "").strip()
    plugin_name = str(plugin_meta.get("name") or "").strip()
    if plugin_desc:
        return f"{plugin_desc} (server: {server_name})"
    if plugin_name:
        return f"MCP catalog server '{server_name}' from plugin '{plugin_name}'."
    return f"MCP catalog server '{server_name}' from {plugin_path}."


def scan_external_mcp_catalog(repo_root: Path) -> list[ToolRecord]:
    external_dir = repo_root / "skills" / "external"
    if not external_dir.is_dir():
        return []

    records: list[ToolRecord] = []
    seen_ids: set[str] = set()

    for mcp_json in sorted(external_dir.rglob(".mcp.json")):
        rel_to_repo = mcp_json.relative_to(repo_root)
        rel_parts = rel_to_repo.parts
        # skills/external/<source_repo>/.../.mcp.json
        if len(rel_parts) < 4:
            continue

        source_repo = rel_parts[2]
        plugin_root = mcp_json.parent
        plugin_rel_parts = rel_parts[3:-1]
        plugin_path = "/".join(plugin_rel_parts) if plugin_rel_parts else plugin_root.name
        domain = plugin_rel_parts[0] if plugin_rel_parts else "general"

        payload = _load_json(mcp_json)
        servers = payload.get("mcpServers")
        if not isinstance(servers, dict):
            continue

        plugin_meta = _plugin_metadata(plugin_root)
        plugin_name = str(plugin_meta.get("name") or plugin_root.name)
        plugin_description = str(plugin_meta.get("description") or "").strip()

        for server_name, cfg in servers.items():
            if not isinstance(cfg, dict):
                cfg = {}
            server_name = str(server_name).strip()
            if not server_name:
                continue

            record_id = f"mcp_catalog:{source_repo}:{plugin_path}:{server_name}"
            if record_id in seen_ids:
                continue
            seen_ids.add(record_id)

            transport = str(cfg.get("type") or "http")
            url = str(cfg.get("url") or "")
            oauth_required = bool(cfg.get("oauth"))
            source_path = rel_to_repo.as_posix()
            tags = [
                "kind:mcp_server",
                "layer:external",
                "catalog_only:true",
                f"source_repo:{source_repo}",
                f"domain:{domain}",
                f"transport:{transport}",
            ]

            records.append(
                ToolRecord(
                    id=record_id,
                    name=server_name,
                    description=_description_for(server_name, plugin_meta, plugin_path),
                    tool_kind="mcp_server",
                    source_path=source_path,
                    metadata={
                        "layer": "external",
                        "source_repo": source_repo,
                        "domain": domain,
                        "catalog_only": True,
                        "executable": False,
                        "plugin_name": plugin_name,
                        "plugin_description": plugin_description,
                        "plugin_path": plugin_path,
                        "source_kind": "external_mcp_catalog",
                        "transport": transport,
                        "url": url,
                        "oauth_required": oauth_required,
                    },
                    invoke={
                        "backend": "catalog_only",
                        "command": "",
                        "args": [],
                        "timeout_ms": 0,
                        "env_keys": [],
                    },
                    tags=tags,
                )
            )

    logger.info("Parsed %d external catalog MCP records from %s", len(records), external_dir)
    return records
