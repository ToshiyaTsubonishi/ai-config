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
#   ./scripts/import-skill.sh <github-repo> [local-name] [--branch <branch>]
#
# Examples:
#   ./scripts/import-skill.sh streamlit/agent-skills streamlit
#   ./scripts/import-skill.sh https://github.com/anthropics/skills anthropics-skills
#   ./scripts/import-skill.sh remotion-dev/skills remotion --branch main
#
# What it does:
#   1. Clones the repo (shallow) into a temp directory
#   2. Finds all skill directories (containing SKILL.md)
#   3. Copies the ENTIRE skill directory tree (scripts/, examples/, etc.)
#   4. Writes provenance metadata to .import.json per skill group
#   5. Optionally rebuilds the selector index
#
# Provenance (.import.json):
#   Each imported skill group gets a .import.json recording:
#     - source_url:    git remote URL
#     - branch:        branch/ref that was cloned
#     - commit_sha:    HEAD commit of the cloned repo
#     - original_paths: paths of SKILL.md files relative to repo root
#     - imported_at:   UTC timestamp of the import
#     - import_tool:   "scripts/import-skill.sh"
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

BRANCH=""
POSITIONAL=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --branch=*)
            BRANCH="${1#*=}"
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

if [ ${#POSITIONAL[@]} -lt 1 ]; then
    echo "Usage: $0 <github-repo-or-url> [local-name] [--branch <branch>]"
    echo ""
    echo "Examples:"
    echo "  $0 streamlit/agent-skills streamlit"
    echo "  $0 https://github.com/anthropics/skills anthropics-skills --branch main"
    exit 1
fi

SOURCE="${POSITIONAL[0]}"

# Derive local name from repo if not provided
if [ ${#POSITIONAL[@]} -ge 2 ]; then
    LOCAL_NAME="${POSITIONAL[1]}"
else
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

CLONE_DIR="$(mktemp -d)"
trap 'rm -rf "$CLONE_DIR"' EXIT

CLONE_ARGS=(--depth 1 --quiet)
if [ -n "$BRANCH" ]; then
    CLONE_ARGS+=(--branch "$BRANCH")
fi

echo "Cloning ${GIT_URL}${BRANCH:+ (branch: ${BRANCH})} ..."
git clone "${CLONE_ARGS[@]}" "$GIT_URL" "$CLONE_DIR/repo"

# Capture provenance from the cloned repo
COMMIT_SHA="$(git -C "$CLONE_DIR/repo" rev-parse HEAD)"
CLONE_BRANCH="$(git -C "$CLONE_DIR/repo" rev-parse --abbrev-ref HEAD)"
IMPORT_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "  Commit: ${COMMIT_SHA}"
echo "  Branch: ${CLONE_BRANCH}"

# --- Find and copy skill directories -----------------------------------------

SKILL_COUNT=0
ORIGINAL_PATHS=()
mkdir -p "$TARGET_DIR"

# Walk the cloned repo for SKILL.md files
while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"

    # Compute the path of SKILL.md relative to repo root
    rel_skill_path="${skill_file#"$CLONE_DIR/repo/"}"
    ORIGINAL_PATHS+=("\"${rel_skill_path}\"")

    # Determine destination
    if [ "$skill_dir" = "$CLONE_DIR/repo" ]; then
        # SKILL.md at repo root → copy repo contents directly into target
        dest="$TARGET_DIR"
    else
        skill_name="$(basename "$skill_dir")"
        dest="${TARGET_DIR}/${skill_name}"
    fi

    mkdir -p "$dest"

    # Copy ENTIRE skill directory tree (scripts/, examples/, resources/, etc.)
    # Use rsync for reliable recursive copy preserving structure
    if command -v rsync &>/dev/null; then
        rsync -a --exclude='.git' "$skill_dir/" "$dest/"
    else
        # Fallback: cp -R (may miss hidden files on some systems)
        cp -R "$skill_dir/." "$dest/" 2>/dev/null || cp -R "$skill_dir"/* "$dest/" 2>/dev/null || true
    fi

    SKILL_COUNT=$((SKILL_COUNT + 1))
    echo "  Imported: ${rel_skill_path%/SKILL.md} → ${dest#"$REPO_ROOT/"}"
done < <(find "$CLONE_DIR/repo" -name "SKILL.md" -not -path "*/.git/*" -print0)

if [ "$SKILL_COUNT" -eq 0 ]; then
    echo "WARNING: No SKILL.md files found in $GIT_URL"
    rmdir "$TARGET_DIR" 2>/dev/null || true
    exit 1
fi

# --- Write provenance metadata ------------------------------------------------

PATHS_JSON=$(IFS=,; echo "${ORIGINAL_PATHS[*]}")

cat > "${TARGET_DIR}/.import.json" <<EOF
{
  "source_url": "${GIT_URL}",
  "branch": "${CLONE_BRANCH}",
  "commit_sha": "${COMMIT_SHA}",
  "original_paths": [${PATHS_JSON}],
  "imported_at": "${IMPORT_TS}",
  "import_tool": "scripts/import-skill.sh",
  "skill_count": ${SKILL_COUNT}
}
EOF

echo ""
echo "Imported ${SKILL_COUNT} skill(s) to ${TARGET_DIR#"$REPO_ROOT/"}"
echo "Provenance saved to ${TARGET_DIR#"$REPO_ROOT/"}/.import.json"

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
