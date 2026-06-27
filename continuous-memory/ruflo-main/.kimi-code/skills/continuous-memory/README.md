。# Continuous Memory Layer

Skill para Kimi Code CLI que implementa memória persistente, sincronizada na nuvem e compartilhável entre agentes (Kimi, Claude, Ruflo).

## Componentes

```
.kimi-code/skills/continuous-memory/
├── SKILL.md
├── README.md
└── scripts/
    ├── init_memory.py           # Inicializa estrutura de memória + cloud
    ├── memory_store.py          # Salva memória em Markdown + Ruflo
    ├── memory_search.py         # Busca memória local + Ruflo
    ├── memory_store.sh          # Wrapper Bash para Kimi
    ├── memory_search.sh         # Wrapper Bash para Kimi
    ├── auto_backup.sh           # Commit/push automático (repo próprio)
    ├── auto_backup_home.sh      # Backup usando repo Git na home
    ├── setup_cloud_backup.py    # Setup automatizado de repo na nuvem
    └── restore_from_cloud.sh    # Restaura memória da nuvem
```

## Configuração atual (ruflo-main)

Este projeto usa o **repositório Git privado já configurado** na pasta home:

```
https://github.com/humbertocarloslouvato-boop/catalogo-puxadores.git
```

A memória contínua é sincronizada em:

```
C:\Users\humbe\continuous-memory\ruflo-main\
```

### Auto-backup ativo

- **Script:** `.kimi-code/skills/continuous-memory/scripts/auto_backup_home.sh`
- **Wrapper Windows:** `C:\Users\humbe\continuous-memory\auto_backup.bat`
- **Tarefa agendada:** `ContinuousMemoryBackup`
- **Frequência:** a cada 15 minutos

### Verificar status do backup

```bash
# Forçar backup manual
bash .kimi-code/skills/continuous-memory/scripts/auto_backup_home.sh

# Ver últimos commits na nuvem
git -C "$HOME" log --oneline -5

# Ver tarefa agendada
cmd //c "schtasks /Query /TN ContinuousMemoryBackup /FO LIST"
```

## Uso via Kimi

```bash
# Salvar uma decisão
bash .kimi-code/skills/continuous-memory/scripts/memory_store.sh \
  "Adotamos ffmpeg" \
  "Por ser universal e scriptável, escolhemos ffmpeg para pipeline de vídeo." \
  decision \
  "video,ffmpeg,decision"

# Buscar memória
bash .kimi-code/skills/continuous-memory/scripts/memory_search.sh \
  "video executor"
```

## Uso via Python

```bash
python .kimi-code/skills/continuous-memory/scripts/memory_store.py \
  --type decision \
  --title "Adotamos ffmpeg" \
  --content "Escolhemos ffmpeg para pipeline de vídeo." \
  --tags "video,ffmpeg" \
  --sync-ruflo

python .kimi-code/skills/continuous-memory/scripts/memory_search.py \
  "video executor" \
  --ruflo
```

## Estrutura de Memória

```
memory/
├── context.md
├── decisions/
├── patterns/
├── projects/
└── agents/

.kimi-code/memory/
├── conversations/
├── decisions/
├── patterns/
├── projects/
└── agents/
```

## Arquitetura

1. **Local Active Memory**: Ruflo AgentDB (`.swarm/memory.db`)
2. **Human-Readable Mirror**: Markdown em `memory/` e `.kimi-code/memory/`
3. **Cloud Backup**: Repositório Git privado
4. **Agent Bridge**: Scripts Bash/Python para Kimi e MCP tools para Claude
