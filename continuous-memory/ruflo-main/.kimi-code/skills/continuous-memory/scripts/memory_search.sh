#!/usr/bin/env bash
# Kimi-compatible wrapper to search memory.
# Usage: memory_search.sh <query>

set -e

QUERY="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python "$SCRIPT_DIR/memory_search.py" "$QUERY" --ruflo
