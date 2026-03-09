"""Parser for MCP server configurations.

Reads MCP server metadata from:
  1. config/master/ai-sync.yaml (`mcp_servers`)
  2. inventory/mcp.*.json snapshots
  3. config/targets/* templates (`*.tmpl`)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    yaml = None

from ai_config.registry.models import ToolRecord
from ai_config.registry.normalization import normalize_targets

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
    "filesystem": "Local filesystem read/write operations",
    "mongodb": "MongoDB database queries and management",
    "terraform": "Terraform infrastructure-as-code operations",
    "webflow": "Webflow CMS and site management",
    "raindrop": "Raindrop.io bookmark collections, items, tags, and search via the hosted MCP endpoint",
    "gemini_cloud_assist": "Google Cloud troubleshooting and investigation",
    "e-stat": "Japanese government statistics (e-Stat) data retrieval",
    "reinfo": "Japanese real estate price data and location info",
    "kkj": "Japanese public procurement information search",
    "line_bot": "LINE messaging bot operations",
    "google_maps": "Google Maps geocoding, directions, and places",
    "inference-proxy-mcp": "Inference Proxy MCP for Whisper and Yomitoku (audio transcription and OCR)",
}


def _extract_first_json_array(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw.startswith("["):
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    return [str(x) for x in parsed if x is not None]


def _extract_env_keys_from_json_object(raw: str) -> list[str]:
    keys: list[str] = []
    for match in re.finditer(r'"([^"]+)"\s*:', raw):
        key = match.group(1).strip()
        if key:
            keys.append(key)
    return sorted(set(keys))


def _rel_to_repo(path: Path) -> str:
    for parent in path.parents:
        if (parent / "config").exists() and (parent / "src").exists():
            try:
                return path.relative_to(parent).as_posix()
            except Exception:
                break
    return path.as_posix()


def _extract_balanced_block(text: str, start_idx: int, open_char: str, close_char: str) -> tuple[str, int] | None:
    depth = 0
    i = start_idx
    in_string = False
    escape = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
        elif ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start_idx : i + 1], i + 1
        i += 1
    return None


def _parse_template_json_mcp(template_path: Path, target: str) -> list[dict[str, Any]]:
    text = template_path.read_text(encoding="utf-8", errors="ignore")
    marker = re.search(r'"mcpServers"\s*:\s*\{', text)
    if not marker:
        return []

    block_start = marker.end() - 1
    block_info = _extract_balanced_block(text, block_start, "{", "}")
    if block_info is None:
        return []
    mcp_servers_block, _ = block_info

    inner = mcp_servers_block[1:-1]
    results: list[dict[str, Any]] = []
    i = 0
    while i < len(inner):
        key_match = re.search(r'"([^"]+)"\s*:\s*\{', inner[i:])
        if not key_match:
            break
        key = key_match.group(1)
        key_open = i + key_match.end() - 1
        value_info = _extract_balanced_block(inner, key_open, "{", "}")
        if value_info is None:
            break
        value_block, value_end = value_info

        command_match = re.search(r'"command"\s*:\s*"([^"]+)"', value_block)
        args_match = re.search(r'"args"\s*:\s*(\[[\s\S]*?\]|[^,\n}]+)', value_block)
        env_match = re.search(r'"env"\s*:\s*(\{[\s\S]*?\})', value_block)
        timeout_match = re.search(r'"timeout_ms"\s*:\s*(\d+)', value_block)

        args = _extract_first_json_array(args_match.group(1)) if args_match else []
        env_keys = _extract_env_keys_from_json_object(env_match.group(1)) if env_match else []
        timeout_ms = int(timeout_match.group(1)) if timeout_match else None

        results.append(
            {
                "name": key,
                "transport": "stdio",
                "command": command_match.group(1) if command_match else None,
                "args": args,
                "enabled_targets": [target],
                "env_keys": env_keys,
                "timeout_ms": timeout_ms,
                "source": _rel_to_repo(template_path),
                "source_kind": "template",
            }
        )
        i = value_end
    return results


def _parse_template_toml_mcp(template_path: Path, target: str) -> list[dict[str, Any]]:
    text = template_path.read_text(encoding="utf-8", errors="ignore")
    section_matches = list(re.finditer(r"^\[mcp_servers\.([^\]]+)\]\s*$", text, flags=re.MULTILINE))
    if not section_matches:
        return []

    results: list[dict[str, Any]] = []
    for idx, match in enumerate(section_matches):
        name = match.group(1).strip()
        section_start = match.end()
        section_end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(text)
        section_body = text[section_start:section_end]

        command_match = re.search(r'^\s*command\s*=\s*"([^"]+)"\s*$', section_body, flags=re.MULTILINE)
        args_match = re.search(r"^\s*args\s*=\s*(\[[\s\S]*?\])\s*$", section_body, flags=re.MULTILINE)
        timeout_match = re.search(r"^\s*timeout_ms\s*=\s*(\d+)\s*$", section_body, flags=re.MULTILINE)
        env_key_matches = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"{{[^"]+}}"', section_body)

        args = _extract_first_json_array(args_match.group(1)) if args_match else []
        timeout_ms = int(timeout_match.group(1)) if timeout_match else None

        results.append(
            {
                "name": name,
                "transport": "stdio",
                "command": command_match.group(1) if command_match else None,
                "args": args,
                "enabled_targets": [target],
                "env_keys": sorted(set(env_key_matches)),
                "timeout_ms": timeout_ms,
                "source": _rel_to_repo(template_path),
                "source_kind": "template",
            }
        )
    return results


def _parse_yaml_file(yaml_path: Path) -> dict[str, Any]:
    if not yaml_path.is_file():
        return {}
    text = yaml_path.read_text(encoding="utf-8", errors="ignore")
    if yaml is not None:
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return _fallback_parse_yaml(text)


def _fallback_parse_yaml(text: str) -> dict[str, Any]:
    """Very small YAML fallback parser for ai-sync keys when pyyaml is unavailable."""
    data: dict[str, Any] = {"targets": {}, "mcp_servers": {}}
    lines = text.splitlines()

    # Parse targets.*.templates.* path strings
    current_target = None
    in_targets = False
    in_templates = False
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "targets:":
            in_targets = True
            in_templates = False
            current_target = None
            continue
        if stripped == "mcp_servers:":
            in_targets = False
            in_templates = False
            current_target = None
            continue

        if in_targets:
            if re.match(r"^\s{2}[A-Za-z0-9_.-]+:\s*$", line):
                current_target = stripped[:-1]
                data["targets"].setdefault(current_target, {"templates": {}})
                in_templates = False
                continue
            if stripped == "templates:" and current_target:
                in_templates = True
                continue
            if in_templates and current_target:
                m = re.match(r'^\s{6}([A-Za-z0-9_.-]+):\s*"([^"]+)"\s*$', line)
                if m:
                    key, value = m.group(1), m.group(2)
                    data["targets"][current_target]["templates"][key] = value

    # Parse mcp_servers block (shallow key extraction).
    in_mcp = False
    current_server = None
    in_env = False
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "mcp_servers:":
            in_mcp = True
            current_server = None
            in_env = False
            continue
        if in_mcp and re.match(r"^[A-Za-z_]", stripped) and not line.startswith(" "):
            # top-level key ended the section
            in_mcp = False
            current_server = None
            in_env = False
            continue
        if not in_mcp:
            continue

        server_match = re.match(r"^\s{2}([A-Za-z0-9_.-]+):\s*$", line)
        if server_match:
            current_server = server_match.group(1)
            data["mcp_servers"][current_server] = {"args": [], "enabled_targets": [], "env": {}}
            in_env = False
            continue
        if not current_server:
            continue

        if re.match(r"^\s{4}env:\s*$", line):
            in_env = True
            continue
        if in_env:
            env_match = re.match(r'^\s{6}([A-Za-z0-9_]+):\s*"?([^"]*)"?\s*$', line)
            if env_match:
                data["mcp_servers"][current_server]["env"][env_match.group(1)] = env_match.group(2)
                continue
            if re.match(r"^\s{4}[A-Za-z0-9_.-]+:", line):
                in_env = False

        cmd_match = re.match(r'^\s{4}command:\s*"([^"]+)"\s*$', line)
        if cmd_match:
            data["mcp_servers"][current_server]["command"] = cmd_match.group(1)
            continue
        timeout_match = re.match(r"^\s{4}timeout_ms:\s*(\d+)\s*$", line)
        if timeout_match:
            data["mcp_servers"][current_server]["timeout_ms"] = int(timeout_match.group(1))
            continue
        target_match = re.match(r"^\s{4}enabled_targets:\s*\[(.*)\]\s*$", line)
        if target_match:
            inside = target_match.group(1).strip()
            if inside:
                arr = [seg.strip().strip('"').strip("'") for seg in inside.split(",")]
                data["mcp_servers"][current_server]["enabled_targets"] = [x for x in arr if x]
            continue
        args_match = re.match(r"^\s{4}args:\s*\[(.*)\]\s*$", line)
        if args_match:
            inside = args_match.group(1).strip()
            if inside:
                arr = [seg.strip().strip('"').strip("'") for seg in inside.split(",")]
                data["mcp_servers"][current_server]["args"] = [x for x in arr if x]

    return data


def _parse_yaml_mcp(yaml_data: dict[str, Any]) -> list[dict[str, Any]]:
    servers = yaml_data.get("mcp_servers", {}) or {}
    results: list[dict[str, Any]] = []
    for name, cfg in servers.items():
        cfg = cfg or {}
        results.append(
            {
                "name": name,
                "transport": cfg.get("transport", "stdio"),
                "command": cfg.get("command"),
                "args": [str(x) for x in cfg.get("args", [])],
                "enabled_targets": [str(x) for x in cfg.get("enabled_targets", [])],
                "env_keys": sorted((cfg.get("env", {}) or {}).keys()),
                "timeout_ms": cfg.get("timeout_ms"),
                "source": "config/master/ai-sync.yaml",
                "source_kind": "master",
            }
        )
    return results


def _parse_inventory_mcp(inventory_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if not inventory_dir.is_dir():
        return results

    for json_path in sorted(inventory_dir.glob("mcp.*.json")):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to parse inventory file: %s", json_path)
            continue

        target = json_path.stem.split(".", 1)[-1] if "." in json_path.stem else ""
        for srv in data.get("servers", []):
            if not srv.get("name"):
                continue
            results.append(
                {
                    "name": srv.get("name", ""),
                    "transport": "stdio",
                    "command": srv.get("command"),
                    "args": [],
                    "enabled_targets": [target] if target else [],
                    "env_keys": [str(x) for x in srv.get("envKeys", [])],
                    "timeout_ms": None,
                    "source": f"inventory/{json_path.name}",
                    "source_kind": "inventory",
                }
            )
    return results


def _parse_target_templates(repo_root: Path, yaml_data: dict[str, Any]) -> list[dict[str, Any]]:
    targets_cfg = yaml_data.get("targets", {}) or {}
    results: list[dict[str, Any]] = []

    for target_name, target_cfg in targets_cfg.items():
        templates = (target_cfg or {}).get("templates", {}) or {}
        for template_path in templates.values():
            rel = str(template_path).strip()
            if not rel.endswith(".tmpl"):
                continue
            template_file = repo_root / rel
            if not template_file.is_file():
                continue

            text = template_file.read_text(encoding="utf-8", errors="ignore")
            if "mcpServers" in text:
                results.extend(_parse_template_json_mcp(template_file, target_name))
            elif "[mcp_servers." in text:
                results.extend(_parse_template_toml_mcp(template_file, target_name))
    return results


def _merge_entries(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    priority = {"master": 3, "template": 2, "inventory": 1}

    for entry in entries:
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        source_kind = str(entry.get("source_kind", "inventory"))
        current = merged.get(name)
        if current is None:
            merged[name] = dict(entry)
            continue

        current_priority = priority.get(str(current.get("source_kind", "inventory")), 0)
        incoming_priority = priority.get(source_kind, 0)

        # Keep richer/high-priority command metadata, always union targets/env keys.
        if incoming_priority >= current_priority:
            for key in ("transport", "command", "args", "timeout_ms", "source", "source_kind"):
                value = entry.get(key)
                if value not in (None, "", []):
                    current[key] = value

        existing_targets = set(current.get("enabled_targets", []) or [])
        existing_targets.update(entry.get("enabled_targets", []) or [])
        current["enabled_targets"] = sorted(existing_targets)

        existing_env = set(current.get("env_keys", []) or [])
        existing_env.update(entry.get("env_keys", []) or [])
        current["env_keys"] = sorted(existing_env)

    return merged


def scan_mcp_servers(repo_root: Path) -> list[ToolRecord]:
    """Scan all MCP config sources and produce deduplicated ToolRecords."""
    yaml_path = repo_root / "config" / "master" / "ai-sync.yaml"
    yaml_data = _parse_yaml_file(yaml_path)

    all_entries: list[dict[str, Any]] = []
    all_entries.extend(_parse_yaml_mcp(yaml_data))
    all_entries.extend(_parse_target_templates(repo_root, yaml_data))
    all_entries.extend(_parse_inventory_mcp(repo_root / "inventory"))

    merged = _merge_entries(all_entries)

    records: list[ToolRecord] = []
    for name, entry in sorted(merged.items()):
        description = _MCP_DESCRIPTIONS.get(name, f"MCP server: {name}")
        enabled_targets = normalize_targets(str(x) for x in (entry.get("enabled_targets", []) or []))
        env_keys = [str(x) for x in (entry.get("env_keys", []) or [])]
        source_path = str(entry.get("source", ""))
        source_repo = "managed"
        domain = "core"
        layer = "managed"
        if source_path.startswith("skills/external/"):
            path_parts = source_path.split("/")
            source_repo = path_parts[2] if len(path_parts) > 2 else "external"
            domain = path_parts[3] if len(path_parts) > 3 else "general"
            layer = "external"
        elif source_path.startswith("inventory/"):
            source_repo = "inventory"
            domain = "inventory"
            layer = "inventory"
        elif source_path.startswith("config/"):
            source_repo = "managed"
            domain = "core"
            layer = "managed"

        tags = ["kind:mcp_server"]
        tags.extend(f"target:{t}" for t in enabled_targets if t)
        tags.append(f"transport:{entry.get('transport', 'stdio')}")

        records.append(
            ToolRecord(
                id=f"mcp:{name}",
                name=name,
                description=description,
                tool_kind="mcp_server",
                source_path=source_path,
                metadata={
                    "layer": layer,
                    "transport": entry.get("transport", "stdio"),
                    "command": entry.get("command"),
                    "args": entry.get("args", []),
                    "enabled_targets": enabled_targets,
                    "env_keys": env_keys,
                    "source_kind": entry.get("source_kind", "unknown"),
                    "source_repo": source_repo,
                    "domain": domain,
                    "catalog_only": False,
                    "executable": True,
                },
                invoke={
                    "backend": "mcp",
                    "command": entry.get("command"),
                    "args": entry.get("args", []),
                    "timeout_ms": entry.get("timeout_ms") or 20000,
                    "env_keys": env_keys,
                },
                tags=tags,
            )
        )

    logger.info("Parsed %d MCP servers", len(records))
    return records
