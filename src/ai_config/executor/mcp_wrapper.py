"""Unified MCP wrapper for tool execution.

Abstracts over different execution backends (MCP stdio, HTTP, skill content)
so the Orchestrator can call any tool through a single interface.

For the Happy Path, most execution is mocked. This module provides the
abstraction layer that will be filled in with real MCP protocol handling.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_config.registry.models import ToolRecord

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a tool."""

    tool_id: str
    status: str  # "success" | "error" | "mock_success"
    output: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
        }


class ToolExecutor:
    """Unified executor that dispatches to the correct backend.

    Execution modes:
      - skill: Returns skill content (instructions for the LLM)
      - mcp_server (stdio): Starts MCP server process, sends JSON-RPC
      - mcp_server (http/sse): Sends HTTP request to running server
    """

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(".")

    def execute(
        self,
        tool: ToolRecord | dict[str, Any],
        action: str = "",
        params: dict[str, Any] | None = None,
        mock: bool = True,
    ) -> ExecutionResult:
        """Execute a tool.

        Args:
            tool: ToolRecord or dict with tool info.
            action: The action/method to invoke.
            params: Parameters for the action.
            mock: If True, simulate execution (Happy Path default).
        """
        if isinstance(tool, dict):
            tool_id = tool.get("id", "unknown")
            tool_type = tool.get("tool_type", "unknown")
        else:
            tool_id = tool.id
            tool_type = tool.tool_type

        if mock:
            return self._mock_execute(tool_id, tool_type, action)

        if tool_type == "skill":
            return self._execute_skill(tool, action)
        elif tool_type == "mcp_server":
            return self._execute_mcp(tool, action, params or {})
        else:
            return ExecutionResult(
                tool_id=tool_id,
                status="error",
                error=f"Unknown tool type: {tool_type}",
            )

    def _mock_execute(self, tool_id: str, tool_type: str, action: str) -> ExecutionResult:
        """Simulate tool execution."""
        logger.info("[MOCK] Executing %s (type=%s, action=%s)", tool_id, tool_type, action)
        return ExecutionResult(
            tool_id=tool_id,
            status="mock_success",
            output=f"Mock execution of {tool_id}: {action}",
        )

    def _execute_skill(
        self, tool: ToolRecord | dict[str, Any], action: str
    ) -> ExecutionResult:
        """Execute a skill by reading its content and returning instructions."""
        if isinstance(tool, dict):
            source_path = tool.get("source_path", "")
            tool_id = tool.get("id", "unknown")
        else:
            source_path = tool.source_path
            tool_id = tool.id

        skill_path = self.repo_root / source_path
        if not skill_path.is_file():
            return ExecutionResult(
                tool_id=tool_id,
                status="error",
                error=f"Skill file not found: {skill_path}",
            )

        content = skill_path.read_text(encoding="utf-8")
        return ExecutionResult(
            tool_id=tool_id,
            status="success",
            output=f"Skill content loaded ({len(content)} chars). "
            f"Use this as instructions to execute the task.",
        )

    def _execute_mcp(
        self,
        tool: ToolRecord | dict[str, Any],
        method: str,
        params: dict[str, Any],
    ) -> ExecutionResult:
        """Execute via MCP stdio protocol (JSON-RPC 2.0).

        This is a simplified implementation. In production, this would
        maintain persistent connections and handle the full MCP lifecycle.
        """
        if isinstance(tool, dict):
            metadata = tool.get("metadata", {})
            tool_id = tool.get("id", "unknown")
        else:
            metadata = tool.metadata
            tool_id = tool.id

        command = metadata.get("command")
        if not command:
            return ExecutionResult(
                tool_id=tool_id,
                status="error",
                error="No command configured for MCP server",
            )

        # Build JSON-RPC request
        rpc_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method or "tools/list",
            "params": params,
        })

        try:
            args = metadata.get("args", [])
            result = subprocess.run(
                [command] + args,
                input=rpc_request,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return ExecutionResult(
                    tool_id=tool_id,
                    status="error",
                    error=f"Process exited with code {result.returncode}: {result.stderr[:200]}",
                )

            return ExecutionResult(
                tool_id=tool_id,
                status="success",
                output=result.stdout[:2000],
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                tool_id=tool_id,
                status="error",
                error="MCP server process timed out",
            )
        except FileNotFoundError:
            return ExecutionResult(
                tool_id=tool_id,
                status="error",
                error=f"Command not found: {command}",
            )
