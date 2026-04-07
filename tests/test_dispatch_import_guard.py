from __future__ import annotations

import importlib
import sys

import pytest


def test_ai_config_dispatch_import_fails_with_external_runtime_guidance() -> None:
    sys.modules.pop("ai_config.dispatch", None)

    with pytest.raises(ImportError) as exc_info:
        importlib.import_module("ai_config.dispatch")

    message = str(exc_info.value)
    assert "ai-config-dispatch" in message
    assert "AI_CONFIG_DISPATCH_CMD" in message


def test_ai_config_dispatch_cli_import_fails_with_same_guidance() -> None:
    sys.modules.pop("ai_config.dispatch", None)
    sys.modules.pop("ai_config.dispatch.cli", None)

    with pytest.raises(ImportError) as exc_info:
        importlib.import_module("ai_config.dispatch.cli")

    message = str(exc_info.value)
    assert "ai-config-dispatch" in message
    assert "ai_config_dispatch.cli" in message
