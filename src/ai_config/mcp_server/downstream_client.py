"""Downstream MCP client helpers for stdio-backed registry MCP servers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from ai_config.executor.command_resolution import default_allowed_command_names, resolve_command_spec
from ai_config.executor.errors import ExecutorError, ExecutorErrorCode
from ai_config.registry.models import ToolRecord


def _dump_model(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _dump_model(value.model_dump())
    if isinstance(value, list):
        return [_dump_model(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _dump_model(item) for key, item in value.items()}
    return value


class DownstreamMCPClient:
    """One-shot MCP client for registry-backed stdio servers."""

    def __init__(self, repo_root: Path, *, allowed_command_names: set[str] | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.allowed_command_names = allowed_command_names or default_allowed_command_names()

    def list_tools(self, record: ToolRecord, *, refresh: bool = False) -> dict[str, Any]:
        del refresh
        return anyio.run(self.list_tools_async, record)

    def call_tool(self, record: ToolRecord, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return anyio.run(self.call_tool_async, record, tool_name, arguments or {})

    async def list_tools_async(self, record: ToolRecord, *, refresh: bool = False) -> dict[str, Any]:
        del refresh
        async with self._session(record) as session:
            tools = await session.list_tools()
            payload = [_dump_model(tool) for tool in tools.tools]
            return {
                "tool_id": record.id,
                "count": len(payload),
                "tools": payload,
            }

    async def call_tool_async(self, record: ToolRecord, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._session(record) as session:
            result = await session.call_tool(tool_name, arguments or {})
            return {
                "tool_id": record.id,
                "tool_name": tool_name,
                "arguments": arguments or {},
                "result": _dump_model(result),
            }

    def _validate_record(self, record: ToolRecord) -> None:
        if record.tool_kind != "mcp_server":
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
                f"Tool is not an MCP server: {record.id}",
                details={"tool_id": record.id, "tool_kind": record.tool_kind},
            )
        if record.metadata.get("executable", True) is False:
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
                f"Tool is catalog-only and not executable: {record.id}",
                details={"tool_id": record.id},
            )
        transport = str(record.metadata.get("transport") or record.invoke.get("transport") or "stdio")
        if transport != "stdio":
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
                f"Unsupported MCP transport for downstream execution: {transport}",
                details={"tool_id": record.id, "transport": transport},
            )

    @asynccontextmanager
    async def _session(self, record: ToolRecord) -> AsyncIterator[ClientSession]:
        self._validate_record(record)
        resolved = resolve_command_spec(
            command=str(record.invoke.get("command") or record.metadata.get("command") or ""),
            args=[str(arg) for arg in (record.invoke.get("args") or record.metadata.get("args") or [])],
            repo_root=self.repo_root,
            env_keys=[str(key) for key in (record.invoke.get("env_keys") or record.metadata.get("env_keys") or [])],
            cwd=".",
            allowed_command_names=self.allowed_command_names,
        )

        params = StdioServerParameters(
            command=resolved.executable,
            args=resolved.args,
            env=resolved.env,
            cwd=resolved.cwd,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
