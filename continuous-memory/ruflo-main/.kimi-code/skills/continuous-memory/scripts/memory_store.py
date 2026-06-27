#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Store a memory entry as Markdown and optionally sync to Ruflo AgentDB.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_encoding():
    """Force UTF-8 for stdout/stderr on Windows/Git Bash."""
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def slugify(text):
    return re.sub(r"[^\w\-]+", "_", text).strip("_").lower()[:60]


def run(cmd, timeout=120, check=False):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0 and check:
        print(f"Command failed: {' '.join(cmd)}")
        print(result.stderr)
    return result


def find_executable(name):
    """Find an executable in PATH using shutil.which (handles .cmd/.exe on Windows)."""
    return shutil.which(name)


def ensure_ruflo_initialized(npx, cwd):
    """Initialize Ruflo memory DB if needed."""
    db_path = Path(cwd) / ".swarm" / "memory.db"
    if db_path.exists():
        return True
    result = run([npx, "claude-flow@latest", "memory", "init"], timeout=300)
    return result.returncode == 0


def sync_to_ruflo(key, content, namespace, tags, cwd):
    """Try to store in Ruflo AgentDB via CLI. Fail silently if Ruflo unavailable."""
    npx = find_executable("npx")
    if not npx:
        print("[RUFLO] npx not found in PATH. Skipping Ruflo sync.")
        return

    ensure_ruflo_initialized(npx, cwd)

    tags_str = ",".join(tags) if isinstance(tags, list) else tags
    # Escape value for shell: replace backslashes first, then quotes, then newlines
    value = content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
    result = run([
        npx, "claude-flow@latest", "memory", "store",
        "--key", key,
        "--value", value,
        "--namespace", namespace,
        "--tags", tags_str
    ], timeout=300)
    if result.returncode == 0:
        print(f"[RUFLO] Stored '{key}' in namespace '{namespace}'")
    else:
        err = result.stderr.strip()[:200] if result.stderr else result.stdout.strip()[:200]
        print(f"[RUFLO] Could not sync: {err}")


def main():
    setup_encoding()
    parser = argparse.ArgumentParser(description="Store a memory entry")
    parser.add_argument("--type", required=True,
                        choices=["decision", "pattern", "conversation", "project", "agent"],
                        help="Memory type")
    parser.add_argument("--title", required=True, help="Short title")
    parser.add_argument("--content", required=True, help="Markdown body content")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--project", default="ruflo-main", help="Project name")
    parser.add_argument("--agent", default="kimi-code-cli", help="Agent name")
    parser.add_argument("--sync-ruflo", action="store_true", help="Sync to Ruflo AgentDB")
    parser.add_argument("--cwd", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.cwd).resolve()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    date = datetime.now(timezone.utc).isoformat()
    slug = slugify(args.title)
    filename = f"{date[:10]}_{slug}.md"

    if args.type == "conversation":
        base_dir = root / ".kimi-code" / "memory" / "conversations"
    elif args.type == "agent":
        base_dir = root / ".kimi-code" / "memory" / "agents"
    else:
        base_dir = root / "memory" / f"{args.type}s"

    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / filename

    frontmatter_tags = ", ".join(f'"{t}"' for t in tags)
    body = f"""---
date: {date}
project: {args.project}
agent: {args.agent}
tags: [{frontmatter_tags}]
summary: "{args.title}"
---

# {args.title}

{args.content}
"""

    file_path.write_text(body, encoding="utf-8")
    print(f"[STORED] {file_path}")

    if args.sync_ruflo:
        namespace = args.type if args.type != "conversation" else "episodic"
        sync_to_ruflo(slug, body, namespace, tags, root)


if __name__ == "__main__":
    main()
