---
date: 2026-06-27T13:59:06.558877+00:00
project: ruflo-main
agent: kimi-code-cli
tags: ["memory", "architecture", "backup", "ruflo", "kimi", "claude"]
summary: "Arquitetura de memória contínua com auto-backup"
---

# Arquitetura de memória contínua com auto-backup

Criamos a Continuous Memory Layer (CML) para persistir contexto entre sessões Kimi/Claude/Ruflo. A arquitetura usa: (1) Ruflo AgentDB como memória ativa local com busca semântica; (2) Markdown mirror em memory/ e .kimi-code/memory/ para legibilidade humana; (3) Repositório Git privado na nuvem com auto-commit/push periódico; (4) Scripts Bash/Python como bridge para Kimi e MCP tools para Claude.
