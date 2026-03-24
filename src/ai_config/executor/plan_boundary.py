"""Execution boundary abstractions for approved plans."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from ai_config.contracts.approved_plan import (
    ApprovedPlanExecutionRequest,
    validate_execution_result_against_request,
)


class ApprovedPlanExecutor(Protocol):
    """Stable interface used by ai-config to hand approved plans to a runtime."""

    def execute_request(self, request: ApprovedPlanExecutionRequest | dict[str, Any]) -> dict[str, Any]:
        """Execute a stable approved-plan request."""


class DispatchCLIPlanExecutor:
    """Dispatch runtime adapter that communicates over a subprocess JSON boundary."""

    def __init__(self, repo_root: Path, *, timeout_seconds: int = 3600) -> None:
        self.repo_root = repo_root.resolve()
        self.timeout_seconds = timeout_seconds

    def _command_prefix(self) -> list[str]:
        override = os.getenv("AI_CONFIG_DISPATCH_CMD", "").strip()
        if override:
            return shlex.split(override)
        return [sys.executable, "-m", "ai_config.dispatch.cli"]

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
        with tempfile.TemporaryDirectory(prefix="ai-config-approved-plan-") as temp_dir:
            request_path = Path(temp_dir) / "approved-plan-request.json"
            request_path.write_text(
                json.dumps(parsed.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            command = [
                *self._command_prefix(),
                "--execute-approved-plan",
                str(request_path),
                "--json",
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=parsed.repo_root or str(self.repo_root),
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
