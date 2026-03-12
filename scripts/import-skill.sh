#!/usr/bin/env bash
# scripts/import-skill.sh — Import external skills into repo-managed skills/external/
#
# Purpose:
#   Fetch skill repos and place them under skills/external/ so that
#   ai-config-index can scan them into the selector index.
#   This maintains selector-first: AI agents never read skills/external/
#   directly; they access these skills only via ai-config-selector.
#
# Usage:
#   ./scripts/import-skill.sh <github-repo> [local-name]
#
# Examples:
#   ./scripts/import-skill.sh streamlit/agent-skills streamlit
#   ./scripts/import-skill.sh https://github.com/anthropics/skills anthropics-skills
#   ./scripts/import-skill.sh remotion-dev/skills remotion
#
# What it does:
#   1. Clones the repo into a temp directory
#   2. Copies skill directories (containing SKILL.md) to skills/external/<name>/
#   3. Optionally rebuilds the selector index
#
# Why not use `npx skills add` directly?
#   vercel-labs/skills installs to agent-specific paths (~/.codex/skills/ etc.)
#   which breaks selector-first. This script targets repo-managed skills/external/.
#
# See docs/constitution.md for architectural rationale.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXTERNAL_DIR="${REPO_ROOT}/skills/external"

# --- Parse arguments ----------------------------------------------------------

if [ $# -lt 1 ]; then
    echo "Usage: $0 <github-repo-or-url> [local-name]"
    echo ""
    echo "Examples:"
    echo "  $0 streamlit/agent-skills streamlit"
    echo "  $0 https://github.com/anthropics/skills anthropics-skills"
    exit 1
fi

SOURCE="$1"

# Derive local name from repo if not provided
if [ $# -ge 2 ]; then
    LOCAL_NAME="$2"
else
    # Extract repo name from URL or shorthand
    LOCAL_NAME="$(echo "$SOURCE" | sed 's|.*/||; s|\.git$||')"
fi

TARGET_DIR="${EXTERNAL_DIR}/${LOCAL_NAME}"

# --- Normalise source to a git URL -------------------------------------------

if [[ "$SOURCE" =~ ^https?:// ]] || [[ "$SOURCE" =~ ^git@ ]]; then
    GIT_URL="$SOURCE"
elif [[ "$SOURCE" =~ ^[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+$ ]]; then
    GIT_URL="https://github.com/${SOURCE}.git"
else
    echo "ERROR: Cannot parse source: $SOURCE"
    exit 1
fi

# --- Clone into temp dir ------------------------------------------------------

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "Cloning ${GIT_URL} ..."
git clone --depth 1 --quiet "$GIT_URL" "$TMPDIR/repo"

# --- Find and copy skills -----------------------------------------------------

SKILL_COUNT=0
mkdir -p "$TARGET_DIR"

# Walk the cloned repo for SKILL.md files
while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"
    skill_name="$(basename "$skill_dir")"

    # If SKILL.md is at repo root, use repo name as skill name
    if [ "$skill_dir" = "$TMPDIR/repo" ]; then
        dest="${TARGET_DIR}"
    else
        dest="${TARGET_DIR}/${skill_name}"
    fi

    mkdir -p "$dest"
    cp -R "$skill_dir"/* "$dest/" 2>/dev/null || true
    SKILL_COUNT=$((SKILL_COUNT + 1))
    echo "  Imported: ${skill_name} → ${dest#"$REPO_ROOT/"}"
done < <(find "$TMPDIR/repo" -name "SKILL.md" -print0)

if [ "$SKILL_COUNT" -eq 0 ]; then
    echo "WARNING: No SKILL.md files found in $GIT_URL"
    rmdir "$TARGET_DIR" 2>/dev/null || true
    exit 1
fi

echo ""
echo "Imported ${SKILL_COUNT} skill(s) to ${TARGET_DIR#"$REPO_ROOT/"}"

# --- Optionally rebuild index -------------------------------------------------

if command -v ai-config-index &>/dev/null; then
    echo ""
    echo "Rebuilding selector index ..."
    ai-config-index --repo-root "$REPO_ROOT"
    echo "Index rebuild complete."
else
    echo ""
    echo "Hint: Run 'ai-config-index' to rebuild the selector index."
fi
