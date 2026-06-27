#!/usr/bin/env bash
# Restore memory from cloud Git repo.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
CLOUD_DIR="$HOME/.continuous-memory/$PROJECT_NAME"

if [ ! -d "$CLOUD_DIR/.git" ]; then
  echo "[ERROR] Cloud backup dir not found: $CLOUD_DIR"
  exit 1
fi

cd "$CLOUD_DIR"
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null

echo "[RESTORE] Memory restored from cloud."
