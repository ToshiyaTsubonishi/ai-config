"""Base adapter interfaces for toolchain command wrappers."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Any, Protocol

from ai_config.executor.errors import ExecutorError, ExecutorErrorCode


class CommandRunner(Protocol):
    def run_command(
        self,
        command: str,
        args: list[str],
        timeout_ms: int,
        env_keys: list[str] | None = None,
    ) -> dict[str, Any]: ...


@dataclass
class BaseAdapter:
    adapter_id: str
    default_command: str
    command_env_var: str

    def command(self) -> str:
        return os.getenv(self.command_env_var, self.default_command)

    def is_available(self) -> bool:
        return shutil.which(self.command()) is not None

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "id": self.adapter_id,
                "backend": "toolchain_adapter",
                "command": self.command(),
                "available": self.is_available(),
            }
        ]

    def call(self, action: str, params: dict[str, Any], runner: CommandRunner) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _require_run_action(action: str) -> None:
        if action not in {"run", "execute", "call", "tools/call"}:
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
                f"Unsupported action for adapter call: {action}",
                details={"allowed_actions": ["run", "execute", "call", "tools/call"]},
            )

