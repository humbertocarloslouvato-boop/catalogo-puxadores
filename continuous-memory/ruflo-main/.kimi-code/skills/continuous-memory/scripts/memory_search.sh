#!/usr/bin/env bash
# Kimi-compatible wrapper to search memory.
# Usage: memory_search.sh <query>

set -e

export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

QUERY="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python "$SCRIPT_DIR/memory_search.py" "$QUERY" --ruflo
