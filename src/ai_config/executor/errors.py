"""Executor error types and structured error codes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExecutorErrorCode(StrEnum):
    EXECUTOR_NOT_AVAILABLE = "EXECUTOR_NOT_AVAILABLE"
    EXECUTOR_NOT_ALLOWED = "EXECUTOR_NOT_ALLOWED"
    EXECUTOR_TIMEOUT = "EXECUTOR_TIMEOUT"
    EXECUTOR_INVALID_ACTION = "EXECUTOR_INVALID_ACTION"
    EXECUTOR_TOOL_NOT_FOUND = "EXECUTOR_TOOL_NOT_FOUND"
    EXECUTOR_RUNTIME_ERROR = "EXECUTOR_RUNTIME_ERROR"


@dataclass
class ExecutorError(Exception):
    code: ExecutorErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}
