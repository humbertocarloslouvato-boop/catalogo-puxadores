#!/usr/bin/env bash
# Auto-backup Continuous Memory Layer to cloud Git repo.
# Run manually or schedule with cron / Task Scheduler.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
CLOUD_DIR="$HOME/.continuous-memory/$PROJECT_NAME"

if [ ! -d "$CLOUD_DIR/.git" ]; then
  echo "[WARN] Cloud backup dir not initialized: $CLOUD_DIR"
  echo "       Run init_memory.py --repo <git-url> first."
  exit 1
fi

cd "$CLOUD_DIR"

# Pull latest changes first to avoid conflicts
git pull --rebase origin main 2>/dev/null || git pull --rebase origin master 2>/dev/null || true

# Add all memory files
git add -A

# Commit only if there are changes
if git diff --cached --quiet; then
  echo "[BACKUP] No changes to commit."
else
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  git commit -m "[memory-backup] $TIMESTAMP - auto sync"
  git push origin HEAD
  echo "[BACKUP] Pushed memory to cloud at $TIMESTAMP"
fi
