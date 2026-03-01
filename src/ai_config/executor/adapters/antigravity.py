"""Antigravity CLI adapter."""

from __future__ import annotations

from ai_config.executor.adapters.base import BaseAdapter, CommandRunner
from ai_config.executor.errors import ExecutorError, ExecutorErrorCode


class AntigravityAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_id="toolchain:antigravity",
            default_command="antigravity",
            command_env_var="AI_CONFIG_ANTIGRAVITY_CMD",
        )

    def call(self, action: str, params: dict[str, object], runner: CommandRunner) -> dict[str, object]:
        self._require_run_action(action)
        if not self.is_available():
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
                f"Antigravity CLI not found: {self.command()}",
                details={"tool_id": self.adapter_id},
            )

        args = [str(x) for x in params.get("args", [])]
        prompt = params.get("prompt")
        if prompt and not args:
            args = ["--prompt", str(prompt)]
        elif prompt:
            args.append(str(prompt))
        if not args:
            args = ["--help"]

        timeout_ms = int(params.get("timeout_ms", 120000))
        env_keys = [str(x) for x in params.get("env_keys", [])]
        return runner.run_command(self.command(), args, timeout_ms=timeout_ms, env_keys=env_keys)

