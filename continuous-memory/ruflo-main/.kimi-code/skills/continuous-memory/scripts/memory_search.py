#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search memory across Markdown mirror and optionally Ruflo AgentDB.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def setup_encoding():
    """Force UTF-8 for stdout/stderr on Windows/Git Bash."""
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def run(cmd, timeout=120):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result


def search_markdown(root, query, limit=10):
    """Search Markdown memory files using ripgrep-like behavior."""
    memory_dirs = [
        root / "memory",
        root / ".kimi-code" / "memory",
    ]

    results = []
    query_lower = query.lower()

    for mem_dir in memory_dirs:
        if not mem_dir.exists():
            continue
        for md_file in mem_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            if query_lower in content.lower():
                # Extract summary from frontmatter or first heading
                summary = ""
                for line in content.splitlines():
                    if line.startswith("summary:"):
                        summary = line.split(":", 1)[1].strip().strip('"')
                        break
                    elif line.startswith("# "):
                        summary = line[2:].strip()
                        break
                results.append({
                    "file": str(md_file.relative_to(root)),
                    "summary": summary or md_file.name,
                })
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return results


def find_executable(name):
    """Find an executable in PATH using shutil.which (handles .cmd/.exe on Windows)."""
    return shutil.which(name)


def search_ruflo(query, limit=5):
    """Try Ruflo semantic search."""
    npx = find_executable("npx")
    if not npx:
        return "[RUFLO] npx not found in PATH. Skipping Ruflo search."

    # Ensure DB is initialized
    db_path = Path(".swarm") / "memory.db"
    if not db_path.exists():
        init = run([npx, "claude-flow@latest", "memory", "init"], timeout=300)
        if init.returncode != 0:
            return f"[RUFLO] Could not initialize memory DB: {init.stderr.strip()[:200]}"

    result = run([
        npx, "claude-flow@latest", "memory", "search",
        "--query", query,
        "--limit", str(limit),
        "--smart"
    ], timeout=300)
    if result.returncode == 0:
        return result.stdout.strip()
    return f"[RUFLO] Search failed: {result.stderr.strip()[:200]}"


def main():
    setup_encoding()
    parser = argparse.ArgumentParser(description="Search memory")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--ruflo", action="store_true", help="Also search Ruflo AgentDB")
    parser.add_argument("--cwd", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.cwd).resolve()

    print(f"\n[SEARCH] '{args.query}' in Markdown memory...")
    md_results = search_markdown(root, args.query, args.limit)
    for r in md_results:
        print(f"  [FILE] {r['file']}: {r['summary']}")

    if args.ruflo:
        print(f"\n[SEARCH] '{args.query}' in Ruflo AgentDB...")
        ruflo_out = search_ruflo(args.query, args.limit)
        print(ruflo_out)


if __name__ == "__main__":
    main()
