"""Parser for MCP server configurations.

Reads from two sources:
  1. config/master/ai-sync.yaml  (mcp_servers section)
  2. inventory/mcp.*.json        (deployed server snapshots)

Produces ToolRecord instances for each unique MCP server.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from ai_config.registry.models import ToolRecord

logger = logging.getLogger(__name__)

# Well-known MCP server descriptions (curated fallback)
_MCP_DESCRIPTIONS: dict[str, str] = {
    "chrome_devtools": "Browser DevTools automation: DOM inspection, screenshots, network monitoring, performance tracing",
    "context7": "Up-to-date documentation and code examples for any programming library or framework",
    "firebase": "Firebase project management, authentication, Firestore, hosting, and cloud functions",
    "firecrawl": "Web scraping, crawling, and content extraction with LLM-optimized markdown output",
    "figma": "Figma design file access and component inspection",
    "github": "GitHub repository management, issues, pull requests, and actions",
    "jina_reader": "Web search, URL reading, screenshot capture, and content extraction",
    "memory": "Knowledge graph for storing and retrieving entities, relations, and observations",
    "notion": "Notion workspace pages, databases, and content management",
    "playwright": "Browser automation for testing and interaction",
    "postgres": "PostgreSQL database queries and schema management",
    "sequential_thinking": "Step-by-step problem decomposition and analysis",
    "slack": "Slack workspace messaging, channels, and user management",
    "sqlite": "SQLite database operations",
    "git": "Git repository operations: commits, branches, diffs",
    "fetch": "HTTP fetch for web content retrieval",
    "eslint": "ESLint code analysis and fixing",
    "filesystem": "Local filesystem read/write operations",
    "mongodb": "MongoDB database queries and management",
    "terraform": "Terraform infrastructure-as-code operations",
    "webflow": "Webflow CMS and site management",
    "gemini_cloud_assist": "Google Cloud troubleshooting and investigation",
    "e-stat": "Japanese government statistics (e-Stat) data retrieval",
    "reinfo": "Japanese real estate price data and location info",
    "kkj": "Japanese public procurement information search",
    "line_bot": "LINE messaging bot operations",
    "google_maps": "Google Maps geocoding, directions, and places",
    "inference-proxy-mcp": "Inference Proxy MCP for Whisper and Yomitoku (audio transcription and OCR)",
}


def _parse_yaml_mcp(yaml_path: Path) -> list[dict[str, Any]]:
    """Extract mcp_servers from ai-sync.yaml."""
    if not yaml_path.is_file():
        return []

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    servers = data.get("mcp_servers", {})
    results = []
    for name, cfg in servers.items():
        results.append(
            {
                "name": name,
                "transport": cfg.get("transport", "stdio"),
                "command": cfg.get("command"),
                "args": cfg.get("args", []),
                "enabled_targets": cfg.get("enabled_targets", []),
                "env_keys": list(cfg.get("env", {}).keys()),
                "source": "ai-sync.yaml",
            }
        )
    return results


def _parse_inventory_mcp(inventory_dir: Path) -> list[dict[str, Any]]:
    """Extract MCP server info from inventory/mcp.*.json files."""
    results = []
    if not inventory_dir.is_dir():
        return results

    for json_path in sorted(inventory_dir.glob("mcp.*.json")):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to parse: %s", json_path)
            continue

        # Infer target from filename: mcp.antigravity.json -> antigravity
        target = json_path.stem.split(".", 1)[-1] if "." in json_path.stem else ""

        for srv in data.get("servers", []):
            results.append(
                {
                    "name": srv.get("name", ""),
                    "transport": "stdio",
                    "command": srv.get("command"),
                    "args_count": srv.get("argsCount", 0),
                    "env_keys": srv.get("envKeys", []),
                    "enabled_targets": [target] if target else [],
                    "source": str(json_path.name),
                }
            )
    return results


def scan_mcp_servers(repo_root: Path) -> list[ToolRecord]:
    """Scan all MCP config sources and produce deduplicated ToolRecords."""
    yaml_entries = _parse_yaml_mcp(repo_root / "config" / "master" / "ai-sync.yaml")
    inventory_entries = _parse_inventory_mcp(repo_root / "inventory")

    # Merge: yaml takes precedence, then add inventory-only servers
    seen: dict[str, dict[str, Any]] = {}
    for entry in yaml_entries:
        seen[entry["name"]] = entry
    for entry in inventory_entries:
        name = entry["name"]
        if name not in seen:
            seen[name] = entry
        else:
            # Merge enabled_targets from inventory
            existing_targets = set(seen[name].get("enabled_targets", []))
            existing_targets.update(entry.get("enabled_targets", []))
            seen[name]["enabled_targets"] = sorted(existing_targets)

    records: list[ToolRecord] = []
    for name, entry in sorted(seen.items()):
        description = _MCP_DESCRIPTIONS.get(name, f"MCP server: {name}")

        records.append(
            ToolRecord(
                id=f"mcp:{name}",
                name=name,
                description=description,
                tool_type="mcp_server",
                source_path=entry.get("source", ""),
                metadata={
                    "transport": entry.get("transport", "stdio"),
                    "command": entry.get("command"),
                    "args": entry.get("args", []),
                    "enabled_targets": entry.get("enabled_targets", []),
                    "env_keys": entry.get("env_keys", []),
                },
            )
        )

    logger.info("Parsed %d MCP servers", len(records))
    return records
