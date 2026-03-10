"""Dynamic tool selection MCP server.

Exposes the ai-config tool registry as an MCP server so that AI agents
can dynamically discover and retrieve tool information without loading
all tools into their context window.

Usage:
    ai-config-mcp-server --repo-root /path/to/ai-config-sync
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from ai_config.executor import ExecutorError, ToolExecutor
from ai_config.mcp_server.downstream_client import DownstreamMCPClient
from ai_config.mcp_server.tools import DEFAULT_TOP_K, ToolIndex
from ai_config.registry.index_builder import DEFAULT_INDEX_DIR
from ai_config.runtime_env import load_runtime_env

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy MCP SDK import – allow import-time safety when mcp is not installed
# ---------------------------------------------------------------------------

_mcp = None


def _get_mcp():
    global _mcp
    if _mcp is None:
        try:
            from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]

            _mcp = FastMCP
        except ImportError:
            logger.error(
                "The 'mcp' package is not installed. "
                "Install it with: pip install 'mcp[cli]>=1.0'"
            )
            sys.exit(1)
    return _mcp


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------


def _json_error(error: ExecutorError | Exception) -> str:
    if isinstance(error, ExecutorError):
        return json.dumps({"status": "error", "error": error.to_dict()}, ensure_ascii=False)
    return json.dumps(
        {
            "status": "error",
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": str(error),
                "details": {},
            },
        },
        ensure_ascii=False,
    )


def create_server(index_dir: Path, repo_root: Path):
    """Create and configure the MCP server with tool definitions."""
    FastMCP = _get_mcp()

    mcp = FastMCP(
        "ai-config-selector",
        instructions=(
            "Dynamic tool selector for ai-config. Searches thousands of "
            "skills and MCP servers to find the best tools for your task."
        ),
    )

    tool_index = ToolIndex(index_dir)
    executor = ToolExecutor(repo_root=repo_root)
    downstream = DownstreamMCPClient(repo_root=repo_root)

    def _refresh_records() -> None:
        executor.register_records(tool_index.records)

    @mcp.tool()
    def search_tools(query: str, top_k: int = DEFAULT_TOP_K) -> str:
        """Search for tools matching a query.

        Returns a compact list of matching tools (name, description, kind).
        Use get_tool_detail for full information on a specific tool.

        Args:
            query: Natural language description of what you need
            top_k: Maximum number of results to return (default 5)
        """
        results = tool_index.search(query, top_k=min(top_k, 10))
        if not results:
            return json.dumps({"message": "No matching tools found.", "results": []})
        return json.dumps({"count": len(results), "results": results}, ensure_ascii=False)

    @mcp.tool()
    def get_tool_detail(tool_id: str) -> str:
        """Get full details for a specific tool by its ID.

        Use search_tools first to find tool IDs.

        Args:
            tool_id: The tool identifier (e.g. 'skill:deep-research', 'mcp:firecrawl')
        """
        detail = tool_index.get_detail(tool_id)
        if detail is None:
            return json.dumps({"error": f"Tool '{tool_id}' not found."})
        return json.dumps(detail, ensure_ascii=False)

    @mcp.tool()
    def list_categories() -> str:
        """List available tool categories and counts.

        Shows how many tools are available by kind (skill, mcp_server, etc.)
        and by layer (external, custom, shared, etc.).
        """
        categories = tool_index.get_categories()
        return json.dumps(categories, ensure_ascii=False)

    @mcp.tool()
    def get_tool_count() -> str:
        """Get the total number of indexed tools."""
        total = len(tool_index.records)
        return json.dumps({"total": total})

    @mcp.tool()
    def execute_registry_tool(tool_id: str, action: str = "run", params: dict[str, Any] | None = None) -> str:
        """Execute a registry-backed tool via the shared executor."""
        try:
            _refresh_records()
            result = executor.tools_call(tool_id=tool_id, action=action, params=params or {})
            return json.dumps(result, ensure_ascii=False)
        except Exception as error:
            return _json_error(error)

    @mcp.tool()
    async def list_mcp_server_tools(tool_id: str, refresh: bool = False) -> str:
        """List tools exposed by an indexed downstream MCP server."""
        try:
            record = tool_index.get_record(tool_id)
            if record is None:
                return json.dumps({"status": "error", "error": {"code": "EXECUTOR_TOOL_NOT_FOUND", "message": f"Tool '{tool_id}' not found.", "details": {"tool_id": tool_id}}}, ensure_ascii=False)
            result = await downstream.list_tools_async(record, refresh=refresh)
            return json.dumps({"status": "success", "output": result}, ensure_ascii=False)
        except Exception as error:
            return _json_error(error)

    @mcp.tool()
    async def call_mcp_server_tool(tool_id: str, tool_name: str, arguments: dict[str, Any] | None = None) -> str:
        """Call a specific tool on an indexed downstream MCP server."""
        try:
            record = tool_index.get_record(tool_id)
            if record is None:
                return json.dumps({"status": "error", "error": {"code": "EXECUTOR_TOOL_NOT_FOUND", "message": f"Tool '{tool_id}' not found.", "details": {"tool_id": tool_id}}}, ensure_ascii=False)
            result = await downstream.call_tool_async(record, tool_name, arguments or {})
            return json.dumps({"status": "success", "output": result}, ensure_ascii=False)
        except Exception as error:
            return _json_error(error)

    return mcp


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="ai-config dynamic tool selector MCP server")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root path",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=None,
        help=f"Index directory (default: <repo-root>/{DEFAULT_INDEX_DIR})",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    index_dir = (args.index_dir or repo_root / DEFAULT_INDEX_DIR).resolve()
    logger.info("Starting ai-config-selector MCP server")
    logger.info("Repo root: %s", repo_root)
    logger.info("Index dir: %s", index_dir)

    mcp = create_server(index_dir, repo_root)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
