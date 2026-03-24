"""Compatibility dispatch runtime.

This package remains in-repo during the migration period, but core
ai-config code reaches it only through the approved-plan boundary.
"""

from ai_config.dispatch.graph import create_dispatch_agent

__all__ = ["create_dispatch_agent"]
