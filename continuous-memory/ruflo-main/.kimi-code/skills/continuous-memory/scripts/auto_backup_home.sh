#!/usr/bin/env bash
# Auto-backup Continuous Memory Layer to the existing cloud Git repo in home.

set -e

HOME_DIR="$HOME"
PROJECT_ROOT="/c/Users/humbe/OneDrive/Área de Trabalho/ruflo-main"
PROJECT_NAME="ruflo-main"
CLOUD_MEMORY_DIR="$HOME_DIR/continuous-memory/$PROJECT_NAME"

echo "[BACKUP] Syncing memory for $PROJECT_NAME..."

# Ensure directories exist
mkdir -p "$CLOUD_MEMORY_DIR/memory"
mkdir -p "$CLOUD_MEMORY_DIR/.kimi-code/memory"
mkdir -p "$CLOUD_MEMORY_DIR/.swarm"
mkdir -p "$CLOUD_MEMORY_DIR/.kimi-code/skills/continuous-memory"

# Copy memory from project to cloud mirror
copy_dir() {
  local src="$1"
  local dst="$2"
  if [ -d "$src" ]; then
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/" 2>/dev/null || cp -r "$src/"* "$dst/"
  fi
}

copy_dir "$PROJECT_ROOT/memory" "$CLOUD_MEMORY_DIR/memory"
copy_dir "$PROJECT_ROOT/.kimi-code/memory" "$CLOUD_MEMORY_DIR/.kimi-code/memory"

# Backup Ruflo AgentDB (vector memory + patterns)
copy_dir "$PROJECT_ROOT/.swarm" "$CLOUD_MEMORY_DIR/.swarm"

# Backup the continuous-memory skill scripts themselves
copy_dir "$PROJECT_ROOT/.kimi-code/skills/continuous-memory" "$CLOUD_MEMORY_DIR/.kimi-code/skills/continuous-memory"

# Go to home git repo and push
cd "$HOME_DIR"

git add -A

if git diff --cached --quiet; then
  echo "[BACKUP] No changes to commit."
else
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  git commit -m "[memory-backup] $TIMESTAMP - auto sync $PROJECT_NAME"
  git push origin main
  echo "[BACKUP] Pushed to cloud at $TIMESTAMP"
fi
