"""Shared command resolution helpers for executor and downstream MCP clients."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ai_config.executor.errors import ExecutorError, ExecutorErrorCode

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

SAFE_BASE_ENV = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "OS",
    "COMSPEC",
}

_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")


@dataclass
class ResolvedCommand:
    executable: str
    args: list[str]
    env: dict[str, str]
    cwd: Path
    allowed_env_values: list[str]
    original_command: str


def default_allowed_command_names(extra_commands: Iterable[str] | None = None) -> set[str]:
    names = set(BASE_ALLOWED_COMMANDS)
    for command in extra_commands or []:
        if not command:
            continue
        names.add(Path(str(command)).name.lower())
    return names


def mask_sensitive(text: str, secret_values: Iterable[str]) -> str:
    masked = text
    for secret in secret_values:
        if not secret or len(secret) < 6:
            continue
        masked = masked.replace(secret, "***")
    masked = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=***", masked)
    return masked


def _build_lookup(repo_root: Path, env_keys: list[str]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    safe_env: dict[str, str] = {}
    lookup: dict[str, str] = {}
    allowed_env_values: list[str] = []

    for key in SAFE_BASE_ENV:
        value = os.environ.get(key)
        if value:
            safe_env[key] = value
            lookup[key] = value

    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    userprofile = os.environ.get("USERPROFILE") or home
    if home:
        safe_env["HOME"] = home
        lookup["HOME"] = home
    if userprofile:
        safe_env["USERPROFILE"] = userprofile
        lookup["USERPROFILE"] = userprofile

    workspace_root = str(repo_root)
    lookup["WORKSPACE_ROOT"] = workspace_root

    for key in env_keys:
        value = os.environ.get(key)
        if value:
            safe_env[key] = value
            lookup[key] = value
            allowed_env_values.append(value)

    return safe_env, lookup, allowed_env_values


def _expand_value(value: str, lookup: dict[str, str]) -> tuple[str, list[str]]:
    missing: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2) or ""
        resolved = lookup.get(key)
        if not resolved:
            missing.append(key)
            return match.group(0)
        return resolved

    return _PLACEHOLDER_RE.sub(_replace, value), missing


def resolve_command_spec(
    *,
    command: str,
    args: list[str],
    repo_root: Path,
    env_keys: list[str] | None = None,
    cwd: str | Path | None = None,
    allowed_command_names: set[str] | None = None,
) -> ResolvedCommand:
    repo_root = repo_root.resolve()
    env_key_list = sorted({str(key) for key in (env_keys or []) if str(key)})
    safe_env, lookup, allowed_env_values = _build_lookup(repo_root, env_key_list)

    expanded_command, missing = _expand_value(str(command or ""), lookup)
    expanded_args: list[str] = []
    for arg in args:
        expanded_arg, arg_missing = _expand_value(str(arg), lookup)
        expanded_args.append(expanded_arg)
        missing.extend(arg_missing)

    run_cwd = cwd if cwd is not None else "."
    expanded_cwd, cwd_missing = _expand_value(str(run_cwd), lookup)
    missing.extend(cwd_missing)

    if missing:
        missing_vars = sorted(set(missing))
        raise ExecutorError(
            ExecutorErrorCode.EXECUTOR_CONFIG_ERROR,
            f"Missing command placeholder values: {', '.join(missing_vars)}",
            details={"missing": missing_vars},
        )

    command_name = Path(expanded_command).name.lower()
    command_stem = Path(expanded_command).stem.lower()
    allowlist = allowed_command_names or default_allowed_command_names()
    if command_name not in allowlist and command_stem not in allowlist:
        raise ExecutorError(
            ExecutorErrorCode.EXECUTOR_NOT_ALLOWED,
            f"Command not allowlisted: {expanded_command}",
            details={"command": expanded_command},
        )

    executable = expanded_command
    if not Path(expanded_command).is_absolute():
        resolved = shutil.which(expanded_command)
        if not resolved:
            raise ExecutorError(
                ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
                f"Command not found: {expanded_command}",
                details={"command": expanded_command},
            )
        executable = resolved
    elif not Path(expanded_command).exists():
        raise ExecutorError(
            ExecutorErrorCode.EXECUTOR_NOT_AVAILABLE,
            f"Command path not found: {expanded_command}",
            details={"command": expanded_command},
        )

    resolved_cwd = Path(expanded_cwd)
    if not resolved_cwd.is_absolute():
        resolved_cwd = (repo_root / resolved_cwd).resolve()
    if not resolved_cwd.exists():
        resolved_cwd = repo_root

    return ResolvedCommand(
        executable=executable,
        args=expanded_args,
        env=safe_env,
        cwd=resolved_cwd,
        allowed_env_values=allowed_env_values,
        original_command=expanded_command,
    )
