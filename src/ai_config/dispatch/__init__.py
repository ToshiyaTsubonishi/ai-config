"""Deprecated entrypoint for the removed in-repo dispatch runtime."""

from __future__ import annotations

_REMOVED_MESSAGE = (
    "ai_config.dispatch has been removed from ai-config. "
    "Dispatch runtime now lives only in the external 'ai-config-dispatch' package. "
    "Install ai-config-dispatch, point AI_CONFIG_DISPATCH_CMD at the external runtime, "
    "or run python -m ai_config_dispatch.cli directly."
)

raise ImportError(_REMOVED_MESSAGE)
