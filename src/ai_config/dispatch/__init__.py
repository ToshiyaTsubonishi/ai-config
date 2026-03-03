"""Multi-agent dispatch orchestrator.

Decomposes user prompts into development steps and delegates each
step to Antigravity / Gemini CLI / Codex CLI as autonomous workers.
"""

from ai_config.dispatch.graph import create_dispatch_agent

__all__ = ["create_dispatch_agent"]
