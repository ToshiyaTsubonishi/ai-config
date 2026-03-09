#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/sync-instructions.sh [pull|push|status] [--dry-run]

Modes:
  pull    Copy runtime files into repository-managed files
  push    Copy repository-managed files into runtime files
  status  Show sync status (default)

Managed pairs:
  instructions/Agent.md   <-> ~/.codex/AGENTS.md
  instructions/Gemini.md  <-> ~/.gemini/GEMINI.md
  instructions/Lesson.md  <-> tasks/lessons.md
USAGE
}

mode="status"
dry_run="false"

for arg in "$@"; do
  case "$arg" in
    pull|push|status)
      mode="$arg"
      ;;
    --dry-run)
      dry_run="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 1
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORE_DIR="$REPO_ROOT/instructions"

files=(
  "agent|$STORE_DIR/Agent.md|$HOME/.codex/AGENTS.md"
  "gemini|$STORE_DIR/Gemini.md|$HOME/.gemini/GEMINI.md"
  "lesson|$STORE_DIR/Lesson.md|$REPO_ROOT/tasks/lessons.md"
)

hash_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "-"
    return
  fi
  shasum -a 256 "$path" | awk '{print $1}'
}

copy_with_log() {
  local src="$1"
  local dest="$2"
  local label="$3"

  if [[ "$dry_run" == "true" ]]; then
    echo "[DRY RUN] $label: $src -> $dest"
    return
  fi

  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "[SYNC] $label: $src -> $dest"
}

run_pull() {
  local row name store runtime
  for row in "${files[@]}"; do
    IFS='|' read -r name store runtime <<< "$row"

    if [[ ! -f "$runtime" ]]; then
      echo "[SKIP] $name: runtime file not found: $runtime"
      continue
    fi

    copy_with_log "$runtime" "$store" "$name"
  done
}

run_push() {
  local row name store runtime
  for row in "${files[@]}"; do
    IFS='|' read -r name store runtime <<< "$row"

    if [[ ! -f "$store" ]]; then
      echo "[SKIP] $name: repository file not found: $store"
      continue
    fi

    copy_with_log "$store" "$runtime" "$name"
  done
}

run_status() {
  local row name store runtime store_hash runtime_hash state

  printf "%-8s %-7s %-7s %-8s %s\n" "NAME" "STORE" "TARGET" "STATE" "TARGET_PATH"
  printf "%-8s %-7s %-7s %-8s %s\n" "--------" "-------" "-------" "--------" "------------------------------"

  for row in "${files[@]}"; do
    IFS='|' read -r name store runtime <<< "$row"

    if [[ -f "$store" ]]; then
      store_hash="$(hash_file "$store")"
      store_state="yes"
    else
      store_hash="-"
      store_state="no"
    fi

    if [[ -f "$runtime" ]]; then
      runtime_hash="$(hash_file "$runtime")"
      runtime_state="yes"
    else
      runtime_hash="-"
      runtime_state="no"
    fi

    if [[ "$store_state" == "yes" && "$runtime_state" == "yes" ]]; then
      if [[ "$store_hash" == "$runtime_hash" ]]; then
        state="synced"
      else
        state="drift"
      fi
    elif [[ "$store_state" == "yes" || "$runtime_state" == "yes" ]]; then
      state="partial"
    else
      state="missing"
    fi

    printf "%-8s %-7s %-7s %-8s %s\n" "$name" "$store_state" "$runtime_state" "$state" "$runtime"
  done
}

case "$mode" in
  pull)
    run_pull
    ;;
  push)
    run_push
    ;;
  status)
    run_status
    ;;
esac
