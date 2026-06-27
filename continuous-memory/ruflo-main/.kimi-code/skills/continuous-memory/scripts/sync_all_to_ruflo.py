#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync all Markdown memory files to Ruflo AgentDB using a single import.
Much faster than individual store calls because it avoids loading the
ONNX embedder once per entry.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def setup_encoding():
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def run(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def find_executable(name):
    return shutil.which(name)


def ensure_ruflo_initialized(npx, cwd):
    db_path = Path(cwd) / ".swarm" / "memory.db"
    if db_path.exists():
        return True
    result = run([npx, "claude-flow@latest", "memory", "init"], timeout=300)
    return result.returncode == 0


def namespace_from_path(md_file, mem_dir):
    parts = md_file.relative_to(mem_dir).parts
    if not parts:
        return "decision"
    ns = parts[0].rstrip("s")
    if ns in ("decision", "pattern", "conversation", "project", "agent"):
        return ns
    return "decision"


def build_export(cwd):
    memory_dirs = [cwd / "memory", cwd / ".kimi-code" / "memory"]
    entries = []
    seen = set()

    for mem_dir in memory_dirs:
        if not mem_dir.exists():
            continue
        for md_file in mem_dir.rglob("*.md"):
            rel = str(md_file.relative_to(cwd))
            namespace = namespace_from_path(md_file, mem_dir)
            key_base = f"{namespace}_{md_file.stem}"[:80]
            key = key_base
            suffix = 1
            while key in seen:
                key = f"{key_base}_{suffix}"
                suffix += 1
            seen.add(key)

            content = md_file.read_text(encoding="utf-8")
            tags = []
            for line in content.splitlines():
                if line.startswith("tags:"):
                    raw = line.split(":", 1)[1].strip().strip("[]")
                    tags = [t.strip().strip('"') for t in raw.split(",") if t.strip()]
                    break

            if namespace == "conversation":
                namespace = "episodic"

            now = int(datetime.now(timezone.utc).timestamp() * 1000)
            entries.append({
                "key": key,
                "namespace": namespace,
                "value": content,
                "tags": ",".join(tags),
                "createdAt": now,
                "updatedAt": now,
                "accessCount": 0,
                "hasEmbedding": False,
                "size": len(content.encode("utf-8"))
            })

    return {
        "schema": "ruflo-memory-export/v1",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "namespace": None,
        "count": len(entries),
        "entries": entries
    }


def main():
    setup_encoding()
    cwd = Path(".").resolve()
    npx = find_executable("npx")
    if not npx:
        print("[RUFLO] npx not found. Aborting.")
        sys.exit(1)

    ensure_ruflo_initialized(npx, cwd)

    export_data = build_export(cwd)
    if export_data["count"] == 0:
        print("[RUFLO] No memory entries to sync.")
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
        export_path = f.name

    try:
        result = run([
            npx, "claude-flow@latest", "memory", "import",
            "-i", export_path,
            "-m", "true"
        ], timeout=300)
        if result.returncode == 0:
            print(f"[RUFLO] Imported {export_data['count']} memory entries.")
            print(result.stdout.strip())
        else:
            print(f"[RUFLO] Import failed: {result.stderr.strip()[:500]}")
            sys.exit(1)
    finally:
        try:
            os.remove(export_path)
        except Exception:
            pass


if __name__ == "__main__":
    main()
