#!/usr/bin/env bash
# Compatibility wrapper for the Phase 1 vendor-layer CLI.
#
# Phase 1 does not directly adopt vercel-labs/skills because upstream does not
# expose the --path behavior this repository needs. The canonical implementation
# lives in ai_config.vendor.cli and keeps skills/external as the stable scan
# target for selector/index/retrieval.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHONPATH_VALUE="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
elif [ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$REPO_ROOT/.venv/Scripts/python.exe"
else
    echo "ERROR: No repo-local Python was found in .venv. Run scripts/setup.sh or scripts/setup.ps1 first."
    exit 1
fi

POSITIONAL=()
PASSTHRU=()
UPDATE_ALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --update)
            UPDATE_ALL=true
            shift
            ;;
        *)
            PASSTHRU+=("$1")
            shift
            ;;
    esac
done

if [ "$UPDATE_ALL" = true ]; then
    exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m ai_config.vendor.cli --repo-root "$REPO_ROOT" update --all "${PASSTHRU[@]}"
fi

if [ ${#PASSTHRU[@]} -lt 1 ]; then
    echo "Usage: $0 <github-repo-or-url-or-local-path> [local-name] [--branch <branch>] [--force] [--dry-run]"
    echo "       $0 --update [--force] [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  $0 streamlit/agent-skills streamlit"
    echo "  $0 anthropics/skills anthropics-skills --branch main"
    echo "  $0 /path/to/local/skills-repo demo-skills"
    echo "  $0 --update"
    exit 1
fi

exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m ai_config.vendor.cli --repo-root "$REPO_ROOT" import "${PASSTHRU[@]}"
