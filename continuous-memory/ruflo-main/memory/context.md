---
date: 2026-06-27T13:52:10.387607+00:00
project: ruflo-main
agent: continuous-memory
tags: [context, project-overview]
summary: "Continuous context for ruflo-main"
---

# ruflo-main — Continuous Context

## Project Overview

Ruflo v3.6 — agent federation and orchestration layer for Claude Code, Kimi Code CLI and other agentic AI tools. Repository located at `C:/Users/humbe/OneDrive/Área de Trabalho/ruflo-main`.

## Technology Stack

- Node.js / TypeScript (Ruflo core)
- Python (automation scripts, video processing)
- ffmpeg (video post-production)
- SQLite + HNSW (Ruflo AgentDB memory)
- ONNX embeddings (memory semantic search)

## Active Goals

1. Maintain Ruflo daemon active for background intelligence
2. Develop reusable Kimi skills (Video Executor, Continuous Memory)
3. Keep memory synchronized across Kimi/Claude/Ruflo sessions

## Key Decisions

See `memory/decisions/`.

## Known Patterns

See `memory/patterns/`.

## Agent Preferences

See `memory/agents/`.
