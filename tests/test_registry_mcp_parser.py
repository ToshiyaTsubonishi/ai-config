from __future__ import annotations

import json
from pathlib import Path

from ai_config.registry.mcp_parser import scan_mcp_servers


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_mcp_parser_merges_master_template_and_inventory(tmp_path: Path) -> None:
    # Make repo-like markers for relative source resolution.
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)

    _write(
        tmp_path / "config" / "master" / "ai-sync.yaml",
        """
targets:
  codex:
    templates:
      config_template: "config/targets/codex/config.toml.tmpl"
mcp_servers:
  alpha:
    transport: "stdio"
    command: "npx"
    args: ["-y", "alpha-server"]
    enabled_targets: ["codex"]
    env: { ALPHA_TOKEN: "{{ALPHA_TOKEN}}" }
    timeout_ms: 12345
""".strip(),
    )

    _write(
        tmp_path / "config" / "targets" / "codex" / "config.toml.tmpl",
        """
[mcp_servers.beta]
command = "npx"
args = ["-y", "beta-server"]
""".strip(),
    )

    inventory_payload = {
        "servers": [
            {"name": "gamma", "command": "npx", "argsCount": 2, "envKeys": ["GAMMA_KEY"]},
            {"name": "alpha", "command": "npx", "argsCount": 1, "envKeys": ["ALPHA_EXTRA"]},
        ]
    }
    inv_path = tmp_path / "inventory" / "mcp.codex.json"
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    inv_path.write_text(json.dumps(inventory_payload), encoding="utf-8")

    records = scan_mcp_servers(tmp_path)
    by_id = {r.id: r for r in records}

    assert "mcp:alpha" in by_id
    assert "mcp:beta" in by_id
    assert "mcp:gamma" in by_id

    alpha = by_id["mcp:alpha"]
    assert alpha.tool_kind == "mcp_server"
    assert alpha.invoke["command"] == "npx"
    assert "codex" in alpha.metadata["enabled_targets"]
    # merged from master + inventory
    assert "ALPHA_TOKEN" in alpha.metadata["env_keys"]
    assert "ALPHA_EXTRA" in alpha.metadata["env_keys"]

