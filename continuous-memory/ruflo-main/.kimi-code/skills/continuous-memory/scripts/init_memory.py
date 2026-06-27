#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize Continuous Memory Layer for a project.

Creates local memory directories and optionally clones/links a cloud Git repo.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


MEMORY_DIRS = [
    "memory/decisions",
    "memory/patterns",
    "memory/projects",
    "memory/agents",
    ".kimi-code/memory/conversations",
    ".kimi-code/memory/decisions",
    ".kimi-code/memory/patterns",
    ".kimi-code/memory/agents",
    ".kimi-code/memory/projects",
]

CONTEXT_TEMPLATE = """---
date: {date}
project: {project}
agent: continuous-memory
tags: [context, project-overview]
summary: "Continuous context for {project}"
---

# {project} — Continuous Context

## Project Overview

[Add a short description of the project.]

## Technology Stack

- 
- 
- 

## Active Goals

1. 
2. 
3. 

## Key Decisions

See `memory/decisions/`.

## Known Patterns

See `memory/patterns/`.

## Agent Preferences

See `memory/agents/`.
"""


def run(cmd, check=True):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Command failed: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    return result


def main():
    parser = argparse.ArgumentParser(description="Initialize Continuous Memory Layer")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--repo", help="Git repo URL for cloud backup")
    parser.add_argument("--cwd", default=".", help="Project root directory")
    args = parser.parse_args()

    root = Path(args.cwd).resolve()

    # Create memory directories
    for d in MEMORY_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"[DIR] {root / d}")

    # Create context.md if not exists
    context_path = root / "memory" / "context.md"
    if not context_path.exists():
        from datetime import datetime, timezone
        date = datetime.now(timezone.utc).isoformat()
        context_path.write_text(CONTEXT_TEMPLATE.format(date=date, project=args.project), encoding="utf-8")
        print(f"[FILE] {context_path}")

    # Cloud backup setup
    if args.repo:
        cloud_dir = Path.home() / ".continuous-memory" / args.project
        cloud_dir.parent.mkdir(parents=True, exist_ok=True)

        if not (cloud_dir / ".git").exists():
            if any(cloud_dir.iterdir()):
                print(f"[WARN] {cloud_dir} exists and is not empty. Skipping clone.")
            else:
                print(f"[GIT] Cloning {args.repo} into {cloud_dir}...")
                run(["git", "clone", args.repo, str(cloud_dir)])
        else:
            print(f"[GIT] {cloud_dir} already a git repo.")

        # Create symlinks for cloud sync
        for local_rel in ["memory", ".kimi-code/memory"]:
            local_path = root / local_rel
            cloud_path = cloud_dir / local_rel
            if not cloud_path.exists():
                cloud_path.symlink_to(local_path.resolve(), target_is_directory=True)
                print(f"[LINK] {cloud_path} -> {local_path}")

        print(f"\n[CLOUD] Backup configured. Run auto_backup.sh to sync.")

    print("\n[OK] Continuous Memory Layer initialized.")


if __name__ == "__main__":
    main()
