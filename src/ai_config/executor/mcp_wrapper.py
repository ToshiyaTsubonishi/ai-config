"""Unified tool execution wrapper with adapter-based backends."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_config.executor.adapters import AntigravityAdapter, CodexAdapter, GeminiCliAdapter
from ai_config.executor.errors import ExecutorError, ExecutorErrorCode
from ai_config.registry.models import ToolRecord


@dataclass
class ExecutionResult:
    tool_id: str
    status: str
    output: Any = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"tool_id": self.tool_id, "status": self.status, "output": self.output, "error": self.error}


class ToolExecutor:
    """Single execution interface for orchestrator and CLI clients."""

    BASE_ALLOWED_COMMANDS = {
        "npx",
        "docker",
        "terraform-mcp-server",
        "cgc",
        "pwsh",
        "powershell",
        "bash",
        "sh",
        "node",
        "python",
        "python3",
    }

    SAFE_BASE_ENV = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE", "OS", "COMSPEC"}

    def __init__(self, repo_root: Path | None = None, records: list[ToolRecord | dict[str, Any]] | None = None):
        self.repo_root = (repo_root or Path(".")).resolve()
        self.adapters = {
            "toolchain:codex": CodexAdapter(),
            "toolchain:gemini_cli": GeminiCliAdapter(),
            "toolchain:antigravity": AntigravityAdapter(),
        }
        self.records_by_id: dict[str, ToolRecord] = {}
        if records:
            self.register_records(records)

    def register_records(self, records: list[ToolRecord | dict[str, Any]]) -> None:
        for record in records:
            if isinstance(record, ToolRecord):
                self.records_by_id[record.id] = record
            else:
                try:
                    parsed = ToolRecord.from_dict(record)
                except Exception:
                    continue
                self.records_by_id[parsed.id] = parsed

    @staticmethod
    def _mask_sensitive(text: str, secret_values: list[str]) -> str:
        masked = text
        for secret in secret_values:
            if not secret or len(secret) < 6:
                continue
            masked = masked.replace(secret, "***")
        masked = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=***", masked)
        return masked

    def _allowed_command_names(self) -> set[str]:
        names = set(self.BASE_ALLOWED_COMMANDS)
        for adapter in self.adapters.values():
            cmd = adapter.command()
            names.add(Path(cmd).name.lower())
        return names

    def run_command(
        self,
        command: str,
        args: list[str],
        timeout_ms: int,
        env_keys: list[str] | None = None,
        cwd: str | Path | None = None,
    ) -> dict[str, Any]:
        cmd_name = Path(command).name.lower()
        if cmd_name not in self._allowed_command_names():
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_NOT_ALLOWED,
                f"Command not allowlisted: {command}",
                details={"command": command},
            )

        executable = command
        if not Path(command).is_absolute():
            resolved = shutil.which(command)
            if not resolved:
                raise ExecutorError(
                    ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
                    f"Command not found: {command}",
                    details={"command": command},
                )
            executable = resolved
        elif not Path(command).exists():
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
                f"Command path not found: {command}",
                details={"command": command},
            )

        safe_env: dict[str, str] = {}
        for key in self.SAFE_BASE_ENV:
            value = os.environ.get(key)
            if value is not None:
                safe_env[key] = value
        allowed_env_values: list[str] = []
        for key in env_keys or []:
            value = os.environ.get(key)
            if value is not None:
                safe_env[key] = value
                allowed_env_values.append(value)

        # Execution context
        run_cwd = (self.repo_root / (cwd or ".")).resolve()
        if not run_cwd.exists():
            run_cwd = self.repo_root

        try:
            proc = subprocess.run(
                [executable, *args],
                cwd=run_cwd,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=max(timeout_ms, 1000) / 1000,
            )
        except subprocess.TimeoutExpired as exc:
            masked_args = [self._mask_sensitive(a, allowed_env_values) for a in args]
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_TIMEOUT,
                self._mask_sensitive(f"Command timed out: {command}", allowed_env_values),
                details={"timeout_ms": timeout_ms, "args": masked_args},
            ) from exc
        except OSError as exc:
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_RUNTIME_ERROR,
                self._mask_sensitive(f"Failed to execute command: {command}", allowed_env_values),
                details={"error": str(exc)},
            ) from exc

        stdout = self._mask_sensitive(proc.stdout or "", allowed_env_values)
        stderr = self._mask_sensitive(proc.stderr or "", allowed_env_values)
        if proc.returncode != 0:
            masked_args = [self._mask_sensitive(a, allowed_env_values) for a in args]
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_RUNTIME_ERROR,
                self._mask_sensitive(f"Command failed: {command}", allowed_env_values),
                details={
                    "exit_code": proc.returncode,
                    "stderr": stderr[:2000],
                    "stdout": stdout[:500],
                    "args": masked_args,
                },
            )

        return {"stdout": stdout[:4000], "stderr": stderr[:2000], "exit_code": proc.returncode}

    def tools_list(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        context = context or {}
        if "records" in context and isinstance(context["records"], list):
            self.register_records(context["records"])

        listed: list[dict[str, Any]] = []
        for adapter in self.adapters.values():
            listed.extend(adapter.list_tools())

        for record in self.records_by_id.values():
            listed.append(
                {
                    "id": record.id,
                    "backend": record.tool_kind,
                    "command": record.invoke.get("command"),
                    "available": True,
                }
            )
        return listed

    def _execute_record(self, record: ToolRecord, action: str, params: dict[str, Any], cwd: str | Path | None = None) -> dict[str, Any]:
        if record.metadata.get("executable", True) is False:
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
                f"Tool is catalog-only and not executable: {record.id}",
                details={"tool_id": record.id},
            )

        if record.tool_kind == "skill":
            skill_path = (self.repo_root / record.source_path).resolve()
            if not skill_path.exists():
                raise ExecutorError(
                    ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
                    f"Skill file not found: {skill_path}",
                    details={"tool_id": record.id},
                )
            content = skill_path.read_text(encoding="utf-8", errors="ignore")
            return {"content_preview": content[:4000], "path": str(skill_path)}

        if record.tool_kind == "toolchain_adapter":
            adapter = self.adapters.get(record.id)
            if not adapter:
                raise ExecutorError(
                    ExecutorErrorCode.EXECUTOR_TOOL_NOT_FOUND,
                    f"Adapter not found for {record.id}",
                    details={"tool_id": record.id},
                )
            # Adapters don't support cwd yet, but we pass it anyway if we update the interface
            return adapter.call(action, params, runner=self)

        if record.tool_kind in {"skill_script", "mcp_server"}:
            command = str(params.get("command") or record.invoke.get("command") or "")
            args = [str(x) for x in (params.get("args") or record.invoke.get("args") or [])]
            timeout_ms = int(params.get("timeout_ms") or record.invoke.get("timeout_ms") or 30000)
            env_keys = [str(x) for x in (params.get("env_keys") or record.invoke.get("env_keys") or [])]

            if not command:
                raise ExecutorError(
                    ExecutorErrorCode.EXECUTOR_RUNTIME_ERROR,
                    f"No command configured for {record.id}",
                    details={"tool_id": record.id},
                )
            return self.run_command(command=command, args=args, timeout_ms=timeout_ms, env_keys=env_keys, cwd=cwd)

        raise ExecutorError(
            ExecutorErrorCode.EXECUTOR_INVALID_ACTION,
            f"Unsupported tool kind for execution: {record.tool_kind}",
            details={"tool_id": record.id},
        )

    def tools_call(self, tool_id: str, action: str, params: dict[str, Any] | None = None, cwd: str | Path | None = None) -> dict[str, Any]:
        params = params or {}
        try:
            if tool_id in self.adapters:
                payload = self.adapters[tool_id].call(action, params, runner=self)
                return {"tool_id": tool_id, "status": "success", "output": payload, "error": None}

            record = self.records_by_id.get(tool_id)
            if not record:
                raise ExecutorError(
                    ExecutorErrorCode.EXECUTOR_TOOL_NOT_FOUND,
                    f"Tool not found in executor registry: {tool_id}",
                    details={"tool_id": tool_id},
                )

            payload = self._execute_record(record, action, params, cwd=cwd)
            return {"tool_id": tool_id, "status": "success", "output": payload, "error": None}
        except ExecutorError as exc:
            return {"tool_id": tool_id, "status": "error", "output": None, "error": exc.to_dict()}

    # Backward compatible facade.
    def execute(
        self,
        tool: ToolRecord | dict[str, Any],
        action: str = "run",
        params: dict[str, Any] | None = None,
        mock: bool = False,
    ) -> ExecutionResult:
        if mock:
            tool_id = tool.id if isinstance(tool, ToolRecord) else str(tool.get("id", "unknown"))
            return ExecutionResult(tool_id=tool_id, status="mock_success", output={"message": "mock execution"})

        if isinstance(tool, ToolRecord):
            self.register_records([tool])
            tool_id = tool.id
        else:
            self.register_records([tool])
            tool_id = str(tool.get("id", "unknown"))

        result = self.tools_call(tool_id=tool_id, action=action, params=params or {})
        return ExecutionResult(tool_id=tool_id, status=result["status"], output=result.get("output"), error=result.get("error"))
