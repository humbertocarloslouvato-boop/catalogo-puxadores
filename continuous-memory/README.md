# Continuous Memory Layer — Cloud Backup

Este repositório armazena a memória contínua dos projetos, sincronizada entre sessões Kimi, Claude e Ruflo.

## Estrutura

```
continuous-memory/
├── README.md
└── ruflo-main/
    ├── memory/
    │   ├── context.md
    │   ├── decisions/
    │   ├── patterns/
    │   ├── projects/
    │   └── agents/
    └── .kimi-code/memory/
        ├── conversations/
        ├── decisions/
        ├── patterns/
        ├── projects/
        └── agents/
```

## Como funciona

- Memória ativa local fica no Ruflo AgentDB (`.swarm/memory.db`)
- Mirror legível em Markdown fica dentro de cada projeto
- Esta pasta na nuvem recebe o backup periódico
- Auto-backup pode ser agendado via cron/Task Scheduler

## Novos projetos

Para adicionar um novo projeto:

```bash
python /caminho/do/projeto/.kimi-code/skills/continuous-memory/scripts/init_memory.py \
  --project "nome-do-projeto"
```

Depois copie a pasta `memory/` e `.kimi-code/memory/` para cá e faça commit/push.
