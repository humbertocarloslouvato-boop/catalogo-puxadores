---
name: "Continuous Memory Layer"
description: "Maintain persistent, cloud-backed memory across Kimi, Claude and Ruflo sessions. Use when the user wants to remember context, decisions, patterns and conversations across sessions, agents or machines, or when setting up auto-backup of project memory."
---

# Continuous Memory Layer (CML)

## What This Skill Does

Implements a **persistent, cloud-backed memory system** that survives session restarts, works across multiple AI agents (Kimi, Claude) and can be synced between machines.

The layer has four parts:

1. **Local Active Memory** — Ruflo AgentDB (`.swarm/memory.db`) for fast semantic search
2. **Human-Readable Mirror** — Markdown files in `memory/` and `.kimi-code/memory/`
3. **Cloud Backup** — Git private repository with auto-commit/push
4. **Agent Bridge** — Scripts that Kimi and Claude can call to read/write memory

## When to Use

- "Lembre-se disso para a próxima sessão"
- "Salve isso na memória do projeto"
- "Configure backup automático da memória"
- "Não quero perder o contexto"
- "Sincronize memória entre Kimi e Claude"
- "Crie um resumo desta conversa"

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLOUD BACKUP                                │
│              github.com/user/project-memory.git                     │
│         (auto-commit + push every 15 min via cron)                  │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ git push / pull
┌─────────────────────────────────────────────────────────────────────┐
│                    HUMAN-READABLE MIRROR                            │
│  memory/                     .kimi-code/memory/                     │
│  ├── context.md              ├── conversations/                     │
│  ├── decisions/              ├── decisions/                         │
│  ├── patterns/               ├── patterns/                          │
│  ├── projects/               └── agents/                            │
│  └── agents/                                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ sync scripts
┌─────────────────────────────────────────────────────────────────────┐
│                    LOCAL ACTIVE MEMORY (Ruflo)                      │
│  .swarm/memory.db  +  .swarm/hnsw.index                             │
│  Semantic search via AgentDB + ONNX embeddings                      │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ MCP / CLI
┌─────────────────────┬─────────────────────┬─────────────────────────┐
│     Kimi CLI        │    Claude Code      │     Ruflo Daemon        │
│  (Bash wrappers)    │   (MCP tools)       │   (background workers)  │
└─────────────────────┴─────────────────────┴─────────────────────────┘
```

## Memory Types

| Type | Location | What to store | Example |
|---|---|---|---|
| **Context** | `memory/context.md` | Project overview, stack, goals | "Ruflo v3.6 project, Node/TS, Kimi+Claude" |
| **Decisions** | `memory/decisions/` | ADRs, important choices | "Adopted ffmpeg for video processing" |
| **Patterns** | `memory/patterns/` | Reusable solutions | "How to fix 401 OAuth in Claude Code" |
| **Conversations** | `.kimi-code/memory/conversations/` | Session summaries | "2026-06-27_video-executor-skill.md" |
| **Projects** | `memory/projects/` | Per-project memory | "marilan-videos.md" |
| **Agents** | `memory/agents/` + `.kimi-code/memory/agents/` | Agent preferences/instructions | "kimi-preferences.md" |

## File Format

Every memory file uses YAML frontmatter + Markdown:

```markdown
---
date: 2026-06-27T13:34:00Z
project: ruflo-main
agent: kimi-code-cli
tags: [decision, video, ffmpeg]
summary: "Created Video Executor skill with multi-agent swarm"
---

# Video Executor Skill

## What was done
...

## Decisions
...

## Next steps
...
```

## Agent Responsibilities

| Agent | Task | Tools |
|---|---|---|
| **Orchestrator** | Decide what to remember and where | `Agent`, `Bash` |
| **Memory Writer** | Create/update Markdown memory files | `Write`, `Edit` |
| **Ruflo Sync Agent** | Push/pull from Ruflo AgentDB | `Bash` (CLI) |
| **Git Backup Agent** | Commit/push memory to cloud | `Bash` (git) |
| **Memory Retriever** | Search and surface relevant context | `Grep`, `Bash`, `Read` |
| **Cross-Agent Bridge** | Translate between Kimi and Claude memory formats | `Read`, `Write` |

## Quick Start

### 1. Initialize memory for a project

```bash
python .kimi-code/skills/continuous-memory/scripts/init_memory.py \
  --project "ruflo-main" \
  --repo "git@github.com:youruser/project-memory.git"
```

### 2. Save a decision

```bash
python .kimi-code/skills/continuous-memory/scripts/memory_store.py \
  --type decision \
  --title "Adopted ffmpeg for video pipeline" \
  --tags "video,ffmpeg,decision" \
  --content "Because ffmpeg is universal and scriptable, we chose it over proprietary tools."
```

### 3. Search memory

```bash
python .kimi-code/skills/continuous-memory/scripts/memory_search.py \
  --query "video executor skill" \
  --limit 5
```

### 4. Auto-backup to cloud

```bash
# Run once to test
bash .kimi-code/skills/continuous-memory/scripts/auto_backup.sh

# Or schedule with cron (Linux/Mac) or Task Scheduler (Windows)
*/15 * * * * bash /path/to/auto_backup.sh
```

## Sync Strategy

Every memory write follows this order:

1. **Write Markdown** in `memory/` or `.kimi-code/memory/`
2. **Sync to Ruflo** via `npx claude-flow memory store` (if Ruflo is active)
3. **Queue for cloud backup** (auto-commit on next cron run)

Every memory read follows this order:

1. Search Ruflo AgentDB via `npx claude-flow memory search`
2. Fallback to `grep` in Markdown mirror
3. Fallback to cloud `git pull` if local missing

## Cloud Backup

The simplest cloud backend is a **private Git repository**.

Why Git:

- Free private repos on GitHub/GitLab
- Version history built-in
- Works offline
- Syncs across machines
- No new API keys needed (just SSH key)

### Setup

1. Create a private repo on GitHub/GitLab: `project-memory`
2. Add SSH key to your account
3. Run init:

```bash
python .kimi-code/skills/continuous-memory/scripts/init_memory.py \
  --repo "git@github.com:youruser/project-memory.git"
```

The script will:
- Clone the repo to `~/.continuous-memory/<project>/`
- Create symlinks to `memory/` and `.kimi-code/memory/`
- Set up auto-backup

## Auto-Backup

The backup script:

1. Exports Ruflo memory snapshot to RVF/Markdown
2. Adds new/modified memory files
3. Commits with timestamp
4. Pushes to cloud repo

```bash
bash .kimi-code/skills/continuous-memory/scripts/auto_backup.sh
```

For Windows Task Scheduler or cron, run it every 15 minutes.

## Cross-Agent Memory

### For Kimi Code CLI

Kimi uses the Bash wrappers in `scripts/`:

```bash
# Store
bash .kimi-code/skills/continuous-memory/scripts/memory_store.sh \
  "pattern-auth" "JWT with refresh tokens" "patterns" "auth,security"

# Search
bash .kimi-code/skills/continuous-memory/scripts/memory_search.sh \
  "authentication patterns"
```

### For Claude Code

Claude uses Ruflo MCP tools directly:

```javascript
mcp__claude-flow__memory_store({
  key: "pattern-auth",
  value: "JWT with refresh tokens",
  namespace: "patterns",
  tags: ["auth", "security"]
});
```

The Continuous Memory Layer syncs both sides every 15 minutes.

## Safety Rules

1. **Never store secrets** (API keys, passwords) in memory files
2. **Use private repos** for cloud backup
3. **Encrypt at rest** if sensitive (Ruflo supports `CLAUDE_FLOW_ENCRYPT_AT_REST=1`)
4. **Review before bulk sync** — memory is append-only by default
5. **Keep files under 1 MB** for fast search

## Recovery

If you lose local memory:

```bash
# Pull from cloud
bash .kimi-code/skills/continuous-memory/scripts/restore_from_cloud.sh

# Or manually
git clone git@github.com:youruser/project-memory.git ~/.continuous-memory/<project>
```

## Future Enhancements

- Vector cloud backend (Pinecone/Weaviate/Qdrant) for semantic search across projects
- Real-time sync via WebHook
- Automatic conversation summarization with LLM
- Cross-project memory federation
