# AUDITORIA COMPLETA — Super Agentes v2
## Data: 13/07/2026 16:35

---

## RESUMO EXECUTIVO

**Status:** PRODUÇÃO ESTÁVEL com dívida técnica acumulada
**Nota geral:** 7.5/10
**Testes:** 25/25 passando ✅
**Deploy:** HTTP 200 ✅
**Bugs críticos:** 3
**Arestas técnicas:** 15

---

## 1. ARQUITETURA

### Estrutura atual (16 arquivos)
```
├── index.html          (1636 linhas, 102KB) ← MONOLÍTICO
├── package.json
├── vercel.json
├── api/
│   ├── pipeline.js     (134 linhas)
│   ├── marketplace-scrape.js (269 linhas)
│   ├── market-analysis.js (96 linhas)
│   ├── proxy.js        (84 linhas)
│   ├── state.js        (56 linhas)
│   ├── ml-scraper.js   (132 linhas) ← OBSOLETO
│   └── ml-test.js      (32 linhas)  ← DEBUG/PROD
├── public/
│   ├── teia.js         (78 linhas)
│   ├── calculos.js     (61 linhas)
│   └── prospect.js     (55 linhas)
├── tests/
│   ├── unit.test.js    (147 linhas)
│   └── integration.test.js (60 linhas)
└── data/
    └── learner_state.json
```

### Problema: Dupla identidade TEIA
```
index.html (linhas 123-182)     → TEIA inline COMPLETO (com localStorage, cloud sync, etc.)
public/teia.js (linhas 4-78)    → TEIA módulo (básico, sem persistência)
```
Os dois objetos TEIA coexistem mas NÃO são o mesmo. O index.html usa o inline.
O módulo public/teia.js é importado mas **suas funções nunca são usadas** pelo código principal.

### Dupla identidade DADOS_NICHOS
```
index.html (linhas 650-675)     → 24 nichos completos
public/prospect.js (linhas 4-9) → 4 nichos básicos
```
Dois datasets separados que podem divergir.

### Quadrupla identidade PROVIDERS
```
index.html     linha 113-118
api/pipeline.js     linha 11-13
api/proxy.js        linha 5-10
api/marketplace-scrape.js  linha 181-186 (hardcoded DeepSeek)
```

---

## 2. BUGS CRÍTICOS (3)

### BUG #1: Código morto causa ReferenceError em runtime
**Arquivo:** index.html, linhas 933-934
```js
// Linhas soltas entre renderMLResults e dispararPipelineCategoria
const termo = document.getElementById('prospTermo').value.trim();
el.innerHTML = `...`;
```
**Impacto:** `termo` e `el` não existem no escopo global. Pode causar erro ao carregar página.
**Causa:** Patch mal aplicado na sessão anterior (sobras de código duplicado).
**Fix:** Remover linhas 933-934.

### BUG #2: Variável `d` fora de escopo em loadFromCloud()
**Arquivo:** index.html, linha 212
```js
async function loadFromCloud() {
  try {
    const r = await fetch('/api/state');
    if (r.ok) {
      const d = await r.json();  // ← d declarado DENTRO do if
      ...
    }
    updateSyncStatus(d?.source === 'kv');  // ← d NÃO existe aqui se r.ok for false
  } catch(e) { updateSyncStatus(false); }
}
```
**Impacto:** `d` é undefined quando fetch retorna não-200, o que funciona por acidente (optional chaining), mas é logicamente errado.
**Fix:** Declarar `let d = null;` antes do try.

### BUG #3: fallback IA silencioso quando sem API key
**Arquivo:** api/marketplace-scrape.js, linha 179
```js
if (scraped.success.length === 0 && api_key) {
```
**Impacto:** Se todos os scrapers falharem E não houver api_key, o usuário vê resultado vazio SEM mensagem de erro.
**Fix:** Adicionar mensagem explícita quando results está vazio.

---

## 3. PROBLEMAS FUNCIONAIS (4)

### 3.1 Arquivos obsoletos em produção
- `api/ml-scraper.js` (132 linhas) — nunca chamado pelo frontend
- `api/ml-test.js` (32 linhas) — arquivo de debug em produção
**Risco:** Aumenta bundle, confunde deploy, pode causar erros se referenciado acidentalmente.

### 3.2 sourcingChina() sem parse robusto
**Arquivo:** index.html, linha 1371
```js
const d = JSON.parse(r.content);
```
Sem try-catch. Se IA retornar markdown ou texto, a função crasha.
**Fix:** Adicionar 4 estratégias de parse como no pipeline.js.

### 3.3 copiarTemplate() recebe parâmetros errados
**HTML (linha 1125):**
```js
onclick="copiarTemplate('${name}','${produto}','${ncm}','${fob}',${moq})"
```
**Função (linha 1152):**
```js
function copiarTemplate(name, produto, moq) {
```
Recebe 5 args, declara 3. Os parâmetros ncm e fob são perdidos.
**Impacto:** Template de cotação não inclui NCM/FOB (dados fiscais importantes).

### 3.4 marketplace-scrape.js summary inconsistente
**Arquivo:** api/marketplace-scrape.js, linhas 258-262
```js
summary: {
  marketplacesScraped: Object.keys(results).length,
  marketplacesWithData: Object.values(results).filter(r => !r.error && !r.blocked).length,
  marketplacesBlocked: Object.values(results).filter(r => r.blocked).length,
  marketplacesError: Object.values(results).filter(r => r.error).length,
}
```
Mas o código cria array `scraped` (linha 12) com `success/blocked/failed/ai` que NUNCA é usado no retorno.
**Fix:** Usar o array `scraped` no summary OU remover o array.

---

## 4. DÍVIDA TÉCNICA (8)

### 4.1 Monólito index.html (1636 linhas, 102KB)
O arquivo principal tem:
- 60 linhas CSS inline
- 160 linhas JS de configuração/estado
- 80 linhas JS de persistência
- 50 linhas JS de navegação
- 1136 linhas JS de 9 abas + funções
- 200 linhas de dados estáticos (DADOS_NICHOS)

**Recomendação:** Extrair para módulos:
```
public/app.js      → configuração, estado, navegação
public/overview.js → aba 1
public/calc.js     → aba 2
public/prosp.js    → aba 3 (prospecção + ranking)
public/copilot.js  → aba 4
public/forn.js     → aba 5
public/intel.js    → aba 6
public/pipeline.js → aba 7
public/ia.js       → aba 8
public/saas.js     → aba 9
```

### 4.2 Testes desatualizados
- integration.test.js testa `ml-scraper.js` (arquivo obsoleto)
- Não testa `marketplace-scrape.js` (novo)
- Não testa `market-analysis.js` (novo)
- Não testa funções do index.html

### 4.3 Segurança — API keys em localStorage
```js
localStorage.setItem('sa_api_keys', JSON.stringify(window.apiKeys));
```
Qualquer XSS pode ler as chaves. Não é ideal para produção SaaS.
**Mitigação recomendada:** Mover para HttpOnly cookies via API state.js.

### 4.4 Sem rate limiting nas APIs
As APIs serverless não têm rate limiting. Um usuário pode esgotar tokens de IA.
**Mitigação:** Vercel tem rate limit nativo, mas deveria ser configurado explicitamente.

### 4.5 marketplace-scrape.js com cheerio desnecessário
```js
import { load } from 'cheerio';
```
Mas o código NÃO usa cheerio no marketplace-scrape.js. Usa fetch direto com regex.
O ml-scraper.js usa cheerio, mas é obsoleto.
**Fix:** Remover import não usado.

### 4.6 Sem CORS headers em marketplace-scrape.js
Enquanto proxy.js e state.js têm headers CORS, marketplace-scrape.js não tem.
Se chamada de domínio diferente, vai falhar.

### 4.7 Hardcoded deepseek no marketplace-scrape fallback
```js
const aiUrl = 'https://api.deepseek.com/v1/chat/completions';
```
Não respeita o provider configurado pelo usuário (pode ser Anthropic, MiniMax, etc.).

### 4.8 Sem cache de resultados de scraping
Cada chamada ao /api/marketplace-scrape faz fetch real. Se o usuário escanear o mesmo produto 2x, faz 2 requisições aos marketplaces.
**Fix:** Adicionar cache simples (TTL 5min) usando Vercel KV.

---

## 5. TESTES — STATUS

### Unitários (25/25) ✅
- calcularCVFF: 4/4
- calcularMargem: 4/4
- calcularLandedCost: 3/3
- TEIA: 4/4
- gerarRanking: 2/2
- DADOS_NICHOS: 1/1
- Integração: 7/7

### Cobertura estimada
- Módulos (public/): ~80%
- APIs: ~40% (falta testar marketplace-scrape e market-analysis)
- Frontend (index.html): ~0% (sem testes de UI)

---

## 6. PLANO DE AÇÃO PRIORIZADO

### P0 — Imediato (hoje)
1. Remover linhas mortas 933-934 do index.html
2. Corrigir escopo de `d` em loadFromCloud()
3. Adicionar mensagem de erro quando scraping falha sem API key
4. Remover api/ml-test.js do deploy

### P1 — Curto prazo (próxima sessão)
5. Corrigir copiarTemplate() para passar NCM/FOB
6. Adicionar parse robusto em sourcingChina()
7. Remover api/ml-scraper.js (substituído por marketplace-scrape.js)
8. Atualizar integration.test.js para testar marketplace-scrape.js
9. Corrigir summary no marketplace-scrape.js

### P2 — Médio prazo
10. Modularizar index.html em 10 arquivos
11. Unificar PROVIDERS em um módulo compartilhado
12. Unificar DADOS_NICHOS
13. Mover TEIA inline para módulo único
14. Adicionar cache no marketplace-scrape.js

### P3 — Longo prazo
15. Migrar API keys para HttpOnly cookies
16. Adicionar rate limiting
17. Testes de UI (Playwright)
18. Adicionar TypeScript gradualmente

---

## 7. VEREDITO

O Super Agentes v2 está **funcional e estável em produção**, com deploy funcionando e 25 testes passando. Porém, carrega **dívida técnica acumulada** de sessões anteriores:

- **3 bugs** que podem causar runtime errors
- **4 arquivos obsoletos/duplicados** no código
- **4 definições duplicadas** de configuração (PROVIDERS)
- **Monólito de 1636 linhas** que dificulta manutenção
- **Testes desatualizados** para novas APIs

**Nota: 7.5/10**
- Funcionalidade: 9/10 (tudo funciona)
- Código limpo: 6/10 (muita duplicação e código morto)
- Testes: 7/10 (bons unitários, faltam integração)
- Segurança: 7/10 (aceitável para protótipo, não para SaaS)
- Manutenibilidade: 6/10 (monólito + duplicação dificultam)
