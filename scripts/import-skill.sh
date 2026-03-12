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
#   ./scripts/import-skill.sh <github-repo> [local-name] [options]
#   ./scripts/import-skill.sh --update [options]
#
# Options:
#   --branch <branch>   Clone a specific branch (default: repo default)
#   --force             Force re-import even if commit SHA is unchanged
#   --update            Walk all .import.json files and re-import each source
#   --dry-run           Show what would happen without making changes
#
# Examples:
#   ./scripts/import-skill.sh streamlit/agent-skills streamlit
#   ./scripts/import-skill.sh anthropics/skills anthropics-skills
#   ./scripts/import-skill.sh remotion-dev/skills remotion --branch main
#   ./scripts/import-skill.sh --update                # re-import all
#   ./scripts/import-skill.sh --update --force         # force re-import all
#
# Provenance (.import.json):
#   Each imported skill group gets a .import.json recording source_url,
#   branch, commit_sha, original_paths, imported_at, updated_at, etc.
#
# See docs/constitution.md for architectural rationale.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXTERNAL_DIR="${REPO_ROOT}/skills/external"

# --- Parse arguments ----------------------------------------------------------

BRANCH=""
FORCE=false
UPDATE_ALL=false
DRY_RUN=false
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
        --force)
            FORCE=true
            shift
            ;;
        --update)
            UPDATE_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

# --- Update mode: walk all .import.json and re-import each -------------------

if [ "$UPDATE_ALL" = true ]; then
    echo "Scanning for .import.json files in ${EXTERNAL_DIR#"$REPO_ROOT/"} ..."
    UPDATED=0
    SKIPPED=0
    FAILED=0

    while IFS= read -r -d '' import_json; do
        dir="$(dirname "$import_json")"
        local_name="$(basename "$dir")"

        # Read source_url and branch from .import.json
        src_url="$(python3 -c "import json; d=json.load(open('$import_json')); print(d.get('source_url',''))" 2>/dev/null || echo "")"
        src_branch="$(python3 -c "import json; d=json.load(open('$import_json')); print(d.get('branch',''))" 2>/dev/null || echo "")"

        if [ -z "$src_url" ]; then
            echo "  SKIP: ${local_name} (no source_url in .import.json)"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        echo ""
        echo "--- Updating: ${local_name} ---"

        ARGS=("$src_url" "$local_name")
        [ -n "$src_branch" ] && ARGS+=(--branch "$src_branch")
        [ "$FORCE" = true ] && ARGS+=(--force)
        [ "$DRY_RUN" = true ] && ARGS+=(--dry-run)

        if "$0" "${ARGS[@]}"; then
            UPDATED=$((UPDATED + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    done < <(find "$EXTERNAL_DIR" -maxdepth 2 -name ".import.json" -print0 2>/dev/null)

    echo ""
    echo "Update complete: ${UPDATED} updated, ${SKIPPED} skipped, ${FAILED} failed"
    exit 0
fi

# --- Single import mode -------------------------------------------------------

if [ ${#POSITIONAL[@]} -lt 1 ]; then
    echo "Usage: $0 <github-repo-or-url> [local-name] [--branch <branch>] [--force] [--dry-run]"
    echo "       $0 --update [--force] [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  $0 streamlit/agent-skills streamlit"
    echo "  $0 anthropics/skills anthropics-skills --branch main"
    echo "  $0 --update                         # re-import all"
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

# --- Check for existing import (re-import detection) --------------------------

EXISTING_JSON="${TARGET_DIR}/.import.json"
INITIAL_IMPORT_TS="$IMPORT_TS"

if [ -f "$EXISTING_JSON" ]; then
    OLD_SHA="$(python3 -c "import json; d=json.load(open('$EXISTING_JSON')); print(d.get('commit_sha',''))" 2>/dev/null || echo "")"
    OLD_IMPORT_TS="$(python3 -c "import json; d=json.load(open('$EXISTING_JSON')); print(d.get('imported_at',''))" 2>/dev/null || echo "")"

    if [ -n "$OLD_IMPORT_TS" ]; then
        INITIAL_IMPORT_TS="$OLD_IMPORT_TS"
    fi

    if [ "$OLD_SHA" = "$COMMIT_SHA" ] && [ "$FORCE" != true ]; then
        echo ""
        echo "Already up to date (SHA: ${COMMIT_SHA:0:12}). Use --force to re-import."
        exit 0
    fi

    if [ "$OLD_SHA" != "$COMMIT_SHA" ]; then
        echo "  Previous: ${OLD_SHA:0:12} → New: ${COMMIT_SHA:0:12}"
    fi
fi

# --- Dry-run check ------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
    echo ""
    SKILL_FILES="$(find "$CLONE_DIR/repo" -name "SKILL.md" -not -path "*/.git/*" | wc -l | tr -d ' ')"
    echo "[dry-run] Would import ${SKILL_FILES} skill(s) to ${TARGET_DIR#"$REPO_ROOT/"}"
    exit 0
fi

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
        dest="$TARGET_DIR"
    else
        skill_name="$(basename "$skill_dir")"
        dest="${TARGET_DIR}/${skill_name}"
    fi

    mkdir -p "$dest"

    # Copy ENTIRE skill directory tree (scripts/, examples/, resources/, etc.)
    if command -v rsync &>/dev/null; then
        rsync -a --delete --exclude='.git' "$skill_dir/" "$dest/"
    else
        # Fallback: remove old content, then copy fresh
        rm -rf "$dest"
        mkdir -p "$dest"
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
  "schema_version": 1,
  "source_url": "${GIT_URL}",
  "branch": "${CLONE_BRANCH}",
  "commit_sha": "${COMMIT_SHA}",
  "original_paths": [${PATHS_JSON}],
  "imported_at": "${INITIAL_IMPORT_TS}",
  "updated_at": "${IMPORT_TS}",
  "import_tool": "scripts/import-skill.sh",
  "skill_count": ${SKILL_COUNT},
  "local_name": "${LOCAL_NAME}"
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
