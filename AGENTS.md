# ai-config Repository Rules

Canonical Codex instructions live in `instructions/Agent.md`.

Before starting work in this repository:
- Read `instructions/Agent.md`.
- Read `tasks/lessons.md`.
- Start with `ai-config-selector` and run `search_tools`.
- If the task spans multiple files, subsystems, or validation areas, use `.venv\Scripts\ai-config-dispatch.cmd` unless the user explicitly forbids dispatch.
- Treat read-only repo inspection, setup validation, MCP validation, and multi-step verification as non-trivial tasks that should default to dispatch, and invoke `.venv\Scripts\ai-config-dispatch.cmd` early.
- If a relevant downstream MCP is executable, verify `list_mcp_server_tools` and `call_mcp_server_tool` before concluding.
