#!/usr/bin/env bash
# Kimi-compatible wrapper to store a memory entry.
# Usage: memory_store.sh <title> <content> <type> <tags>

set -e

export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

TITLE="$1"
CONTENT="$2"
TYPE="${3:-pattern}"
TAGS="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python "$SCRIPT_DIR/memory_store.py" \
  --type "$TYPE" \
  --title "$TITLE" \
  --content "$CONTENT" \
  --tags "$TAGS" \
  --sync-ruflo
