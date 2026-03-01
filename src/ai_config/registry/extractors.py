"""Registry extractor aggregator.

Collects all registry records from skills, scripts, MCP servers and toolchain adapters.
"""

from __future__ import annotations

from pathlib import Path

from ai_config.registry.mcp_parser import scan_mcp_servers
from ai_config.registry.models import ToolRecord
from ai_config.registry.script_parser import scan_skill_scripts
from ai_config.registry.skill_parser import scan_skills


def _toolchain_adapters(repo_root: Path) -> list[ToolRecord]:
    return [
        ToolRecord(
            id="toolchain:codex",
            name="codex",
            description="Codex CLI adapter for unified execution",
            tool_kind="toolchain_adapter",
            source_path=(repo_root / "src/ai_config/executor/adapters/codex.py").relative_to(repo_root).as_posix(),
            metadata={"backend": "codex"},
            invoke={
                "backend": "cli",
                "command": "codex",
                "args": [],
                "timeout_ms": 120000,
                "env_keys": [],
            },
            tags=["toolchain:codex", "capability:cli_execution"],
        ),
        ToolRecord(
            id="toolchain:gemini_cli",
            name="gemini_cli",
            description="Gemini CLI adapter for unified execution",
            tool_kind="toolchain_adapter",
            source_path=(repo_root / "src/ai_config/executor/adapters/gemini_cli.py").relative_to(repo_root).as_posix(),
            metadata={"backend": "gemini_cli"},
            invoke={
                "backend": "cli",
                "command": "gemini",
                "args": [],
                "timeout_ms": 120000,
                "env_keys": [],
            },
            tags=["toolchain:gemini_cli", "capability:cli_execution"],
        ),
        ToolRecord(
            id="toolchain:antigravity",
            name="antigravity",
            description="Antigravity CLI adapter for unified execution",
            tool_kind="toolchain_adapter",
            source_path=(repo_root / "src/ai_config/executor/adapters/antigravity.py").relative_to(repo_root).as_posix(),
            metadata={"backend": "antigravity"},
            invoke={
                "backend": "cli",
                "command": "antigravity",
                "args": [],
                "timeout_ms": 120000,
                "env_keys": [],
            },
            tags=["toolchain:antigravity", "capability:cli_execution"],
        ),
    ]


def collect_all_records(repo_root: Path) -> list[ToolRecord]:
    """Collect and merge all registry records from every extractor."""
    records: list[ToolRecord] = []
    records.extend(scan_skills(repo_root))
    records.extend(scan_skill_scripts(repo_root))
    records.extend(scan_mcp_servers(repo_root))
    records.extend(_toolchain_adapters(repo_root))

    deduped: list[ToolRecord] = []
    seen: set[str] = set()
    for record in records:
        if record.id in seen:
            continue
        seen.add(record.id)
        deduped.append(record)
    return deduped
