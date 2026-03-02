from __future__ import annotations

import json
from pathlib import Path

from ai_config.registry.external_mcp_catalog_parser import scan_external_mcp_catalog


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_scan_external_mcp_catalog_parses_servers_and_plugin_metadata(tmp_path: Path) -> None:
    plugin_root = tmp_path / "skills" / "external" / "anthropics-knowledge-work-plugins" / "sales"
    _write_json(
        plugin_root / ".mcp.json",
        {
            "mcpServers": {
                "slack": {"type": "http", "url": "https://mcp.slack.com/mcp"},
                "hubspot": {"type": "http", "url": "https://mcp.hubspot.com/mcp"},
            }
        },
    )
    _write_json(
        plugin_root / ".claude-plugin" / "plugin.json",
        {
            "name": "sales",
            "description": "Sales role plugin",
            "version": "1.0.0",
        },
    )

    records = scan_external_mcp_catalog(tmp_path)
    assert len(records) == 2
    ids = {r.id for r in records}
    assert "mcp_catalog:anthropics-knowledge-work-plugins:sales:slack" in ids
    assert "mcp_catalog:anthropics-knowledge-work-plugins:sales:hubspot" in ids

    slack = next(r for r in records if r.name == "slack")
    assert slack.tool_kind == "mcp_server"
    assert slack.metadata["catalog_only"] is True
    assert slack.metadata["executable"] is False
    assert slack.metadata["source_repo"] == "anthropics-knowledge-work-plugins"
    assert slack.metadata["domain"] == "sales"
    assert slack.metadata["plugin_name"] == "sales"
    assert "Sales role plugin" in slack.description


def test_scan_external_mcp_catalog_without_plugin_json_uses_fallback_description(tmp_path: Path) -> None:
    plugin_root = tmp_path / "skills" / "external" / "anthropics-knowledge-work-plugins" / "data"
    _write_json(
        plugin_root / ".mcp.json",
        {"mcpServers": {"bigquery": {"type": "http", "url": "https://bigquery.googleapis.com/mcp"}}},
    )

    records = scan_external_mcp_catalog(tmp_path)
    assert len(records) == 1
    rec = records[0]
    assert rec.name == "bigquery"
    assert rec.metadata["plugin_name"] == "data"
    assert rec.metadata["catalog_only"] is True
    assert "bigquery" in rec.description.lower()
