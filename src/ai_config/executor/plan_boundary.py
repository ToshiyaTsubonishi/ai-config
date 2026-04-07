"""Execution boundary abstractions for approved plans."""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from ai_config.contracts.approved_plan import (
    ApprovedPlanExecutionRequest,
    validate_execution_result_against_request,
)

_PRODUCTION_HINT_ENV_KEYS = ("K_SERVICE", "K_REVISION", "CLOUD_RUN_JOB")


@dataclass(frozen=True)
class DispatchRuntimeResolution:
    mode: str
    source: str
    command_prefix: tuple[str, ...] | None
    env: dict[str, str] | None = None
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source": self.source,
            "command_prefix": list(self.command_prefix) if self.command_prefix is not None else None,
            "env": dict(self.env) if self.env is not None else None,
            "message": self.message,
        }


class ApprovedPlanExecutor(Protocol):
    """Stable interface used by ai-config to hand approved plans to a runtime."""

    def execute_request(self, request: ApprovedPlanExecutionRequest | dict[str, Any]) -> dict[str, Any]:
        """Execute a stable approved-plan request."""


class DispatchCLIPlanExecutor:
    """Dispatch runtime adapter that communicates over a subprocess JSON boundary."""

    def __init__(self, repo_root: Path, *, timeout_seconds: int = 3600) -> None:
        self.repo_root = repo_root.resolve()
        self.timeout_seconds = timeout_seconds
        self._ai_config_repo_root = Path(__file__).resolve().parents[3]

    def _runtime_mode(self) -> str:
        configured = os.getenv("AI_CONFIG_DISPATCH_RUNTIME_MODE", "").strip().lower()
        if configured:
            if configured == "auto":
                configured = ""
            elif configured not in {"local", "production"}:
                raise ValueError(
                    "AI_CONFIG_DISPATCH_RUNTIME_MODE must be one of: auto, local, production."
                )

        if configured:
            return configured
        if any(os.getenv(name, "").strip() for name in _PRODUCTION_HINT_ENV_KEYS):
            return "production"
        return "local"

    def _ai_config_checkout_root(self) -> Path:
        candidate = self.repo_root
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "ai_config").exists():
            return candidate
        fallback = self._ai_config_repo_root
        if (fallback / "pyproject.toml").exists() and (fallback / "src" / "ai_config").exists():
            return fallback
        return candidate

    def _external_repo_root(self) -> Path | None:
        candidate = self._ai_config_checkout_root().parent / "ai-config-dispatch"
        if not (candidate / "pyproject.toml").exists():
            return None
        if not (candidate / "src" / "ai_config_dispatch" / "cli.py").exists():
            return None
        return candidate

    def _sibling_env(self, external_repo: Path) -> dict[str, str]:
        env = dict(os.environ)
        python_paths = [
            str(external_repo / "src"),
            str(self._ai_config_checkout_root() / "src"),
        ]
        existing = env.get("PYTHONPATH", "")
        if existing:
            python_paths.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(python_paths)
        env.setdefault("AI_CONFIG_DISPATCH_WORKFLOW_DIR", str(external_repo / "workflows"))
        return env

    @staticmethod
    def _installed_module_command() -> list[str] | None:
        try:
            spec = importlib.util.find_spec("ai_config_dispatch.cli")
        except (ImportError, ValueError):
            return None
        if spec is None:
            return None
        return [sys.executable, "-m", "ai_config_dispatch.cli"]

    def _resolve_runtime(self) -> DispatchRuntimeResolution:
        override = os.getenv("AI_CONFIG_DISPATCH_CMD", "").strip()
        mode = self._runtime_mode()
        if override:
            return DispatchRuntimeResolution(
                mode=mode,
                source="override",
                command_prefix=tuple(shlex.split(override)),
            )

        if mode == "local":
            external_repo = self._external_repo_root()
            if external_repo is not None:
                return DispatchRuntimeResolution(
                    mode=mode,
                    source="sibling_checkout",
                    command_prefix=(sys.executable, "-m", "ai_config_dispatch.cli"),
                    env=self._sibling_env(external_repo),
                )

        installed = shutil.which("ai-config-dispatch")
        if installed:
            return DispatchRuntimeResolution(
                mode=mode,
                source="installed_binary",
                command_prefix=(installed,),
            )

        installed_module = self._installed_module_command()
        if installed_module is not None:
            return DispatchRuntimeResolution(
                mode=mode,
                source="installed_module",
                command_prefix=tuple(installed_module),
            )

        if mode == "production":
            message = (
                "Dispatch runtime is unavailable in production mode. "
                "Set AI_CONFIG_DISPATCH_CMD or install ai-config-dispatch in the image. "
                "sibling checkout and in-repo runtime are disabled in production."
            )
        else:
            message = (
                "Dispatch runtime is unavailable in local mode. "
                "Set AI_CONFIG_DISPATCH_CMD, clone ../ai-config-dispatch, or install ai-config-dispatch. "
                "The in-repo ai_config.dispatch runtime has been removed from ai-config."
            )
        return DispatchRuntimeResolution(
            mode=mode,
            source="unavailable",
            command_prefix=None,
            message=message,
        )

    def describe_runtime_resolution(self) -> dict[str, Any]:
        return self._resolve_runtime().as_dict()

    def _command_prefix(self) -> list[str]:
        resolution = self._resolve_runtime()
        if resolution.command_prefix is None:
            raise RuntimeError(resolution.message)
        return list(resolution.command_prefix)

    @staticmethod
    def _error_result(message: str, *, final_report: str = "", returncode: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "error",
            "final_report": final_report,
            "error": message,
        }
        if returncode is not None:
            payload["returncode"] = returncode
        return payload

    def execute_request(self, request: ApprovedPlanExecutionRequest | dict[str, Any]) -> dict[str, Any]:
        parsed = request if isinstance(request, ApprovedPlanExecutionRequest) else ApprovedPlanExecutionRequest.model_validate(request)
        try:
            resolution = self._resolve_runtime()
        except ValueError as exc:
            return self._error_result(str(exc))
        if resolution.command_prefix is None:
            return self._error_result(resolution.message)
        with tempfile.TemporaryDirectory(prefix="ai-config-approved-plan-") as temp_dir:
            request_path = Path(temp_dir) / "approved-plan-request.json"
            request_path.write_text(
                json.dumps(parsed.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            command = [
                *resolution.command_prefix,
                "--execute-approved-plan",
                str(request_path),
                "--json",
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=parsed.repo_root or str(self.repo_root),
                env=resolution.env,
                timeout=self.timeout_seconds,
            )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if not stdout:
            return self._error_result(
                stderr or "Dispatch returned no stdout payload.",
                returncode=result.returncode if result.returncode != 0 else None,
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return self._error_result(
                "Dispatch returned non-JSON output.",
                final_report=stdout,
                returncode=result.returncode if result.returncode != 0 else None,
            )

        if not isinstance(payload, dict):
            return self._error_result(
                "Dispatch returned an invalid JSON payload.",
                returncode=result.returncode if result.returncode != 0 else None,
            )

        try:
            validated = validate_execution_result_against_request(payload, parsed)
        except (ValidationError, ValueError) as exc:
            return self._error_result(
                f"Invalid execution result payload: {exc}",
                returncode=result.returncode if result.returncode != 0 else None,
            )

        return validated.model_dump()
