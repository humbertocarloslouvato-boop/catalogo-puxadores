// API Pipeline v2 — Integrado com skill china-brazil-import-strategy
// Iron Rules + Decision Tree + Marketplace Intelligence 10 pontos
// POST /api/pipeline { category, api_key, provider }

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  try {
    const { category, api_key, provider } = req.body || {};
    if (!category || !api_key) return res.status(400).json({ error: 'category e api_key obrigatórios' });

    const PROVIDERS = {
      deepseek: { url: 'https://api.deepseek.com/v1/chat/completions', model: 'deepseek-chat' },
      minimax: { url: 'https://api.minimax.chat/v1/text/chatcompletion_v2', model: 'MiniMax-Text-01' },
      zai: { url: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', model: 'glm-4' },
    };
    const pr = PROVIDERS[provider || 'deepseek'];
    if (!pr) return res.status(400).json({ error: 'provider inválido' });

    const catNome = category;
    const IRON_RULES = `REGRAS DE OURO (Iron Rules do skill china-brazil-import-strategy):
1. NUNCA importe sem RADAR aprovado (30-60 dias lead time)
2. SEMPRE valide NCM com despachante antes de fechar pedido
3. SEMPRE peça amostras físicas antes da produção
4. SEMPRE use Trade Assurance ou L/C no primeiro pedido (30% upfront + 70% contra BL)
5. SEMPRE contrate SGS/Bureau Veritas para inspeção pré-embarque (primeiro pedido)
6. NUNCA use NCM que não encaixa — Customs reclassifica com multa 75-150%
7. NUNCA subestime lead time — primeira importação leva 110-130 dias na prática
8. NUNCA pule consolidação Master LCL — 6-8 SKUs em 1 LCL economiza ~50% frete`;

    const DECISION_TREE = `ÁRVORE DE DECISÃO:
- Volume < 1m³ → DHL courier (mais barato que LCL)
- Volume 1-12m³ → LCL (use Master LCL se multi-SKU)
- Volume 12-28m³ → FCL 20ft
- Volume > 28m³ → FCL 40ft ou 40HQ
- Eletrônicos → INMETRO 3-6 meses, R$15-30k
- Saúde/médico → ANVISA 6-12 meses, R$50-100k
- Wireless/Bluetooth → ANATEL 8-16 semanas, R$8-15k
- Pet food/suplemento → MAPA CADPET 30-60 dias, R$2-5k`;

    const prompt = `Você é um Discovery Agent do skill china-brazil-import-strategy.

${IRON_RULES}

${DECISION_TREE}

Para a categoria "${catNome}", identifique 6-8 nichos subexplorados no e-commerce brasileiro com alto potencial de importação da China.

Use a metodologia de 10 pontos do Marketplace Intelligence:
1. TOP SELLERS: quem domina o nicho
2. PRICE DISTRIBUTION: P25/P50/P75/P90
3. BEST SELLERS: top produtos por avaliações
4. EMERGING TRENDS: o que está crescendo
5. UNTAPPED NICHES: subnichos sem concorrência
6. CATALOG GAPS: o que falta nos top sellers
7. CUSTOMER PAIN POINTS: reclamações recorrentes
8. PRICING OPPORTUNITIES: gap premium e gap value
9. BARRIER TO ENTRY: capital, certificação, marca
10. RECOMMENDATION: veredito + preço-alvo + diferenciação

Matriz de score: margem(25%) + demanda(20%) + concorrência_inversa(20%) + time-to-market(15%) + regulatório(10%) + investimento(10%)
Score > 70 = GO, 50-70 = COND, < 50 = NO-GO

Para cada nicho informe:
- nome: nome curto do produto
- ncm: NCM Brasil (formato 0000.00.00)
- fob: preço FOB USD (preço de FÁBRICA no 1688 com MOQ 300+, tipicamente 30-50% do varejo)
- landed: custo landed estimado BRL (fob × 5.2 × fator impostos ~1.7-1.9)
- preco: preço venda sugerido BRL
- concorrencia: descrição resumida
- score: 0-100
- recomendacao: GO/COND/NO-GO
- regulacao: certificação necessária (INMETRO/ANVISA/ANATEL/MAPA/nenhuma)
- volume_m3: volume unitário estimado
- decisao_modal: recomendação de frete (COURIER/LCL/FCL)

Retorne APENAS JSON: {"nichos":[{...}]}`;

    const r1 = await fetch(pr.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${api_key}` },
      body: JSON.stringify({ model: pr.model, messages: [{ role: 'user', content: prompt }], max_tokens: 2000, temperature: 0.7 }),
    });
    const d1 = await r1.json();
    if (!r1.ok) return res.status(r1.status).json({ error: d1.error?.message || 'Discovery falhou', raw: d1 });

    const content = d1.choices?.[0]?.message?.content || '';
    let data;
    try {
      const jsonStart = content.indexOf('{');
      const jsonEnd = content.lastIndexOf('}');
      data = JSON.parse(content.substring(jsonStart, jsonEnd + 1));
    } catch {
      return res.status(500).json({ error: 'JSON inválido da IA', raw: content.substring(0, 300) });
    }

    const nichos = (data.nichos || []).map(n => {
      const score = parseInt(n.score) || 50;
      const confiancaIA = n.confidence || (score >= 80 ? 0.85 : score >= 60 ? 0.7 : 0.5);

      // Truth Engine: classificar nível de verdade
      const truth = (score >= 80 && confiancaIA >= 0.8) ? 'source_observed' :
                    (score >= 60 && confiancaIA >= 0.6) ? 'cross_checked' :
                    (confiancaIA >= 0.4) ? 'estimated' : 'unavailable';

      const truthLabels = {
        unavailable: '🔴 Sem dados reais',
        estimated: '🟡 Estimativa IA',
        source_observed: '🟢 Observado na fonte',
        cross_checked: '✅ Verificado (2+ fontes)',
        quote_confirmed: '🏆 Cotação confirmada',
        outcome_confirmed: '⭐ Resultado real'
      };

      // insufficient_data: se confiança < 0.5 e score < 60
      const recomendacaoFinal = (confiancaIA < 0.5 && score < 60) ? 'insufficient_data' :
                                 (n.recomendacao || n.recommendation || (score >= 70 ? 'GO' : score >= 50 ? 'COND' : 'NO-GO'));

      return {
        nome: n.nome || n.name || '',
        ncm: n.ncm || '0000.00.00',
        fob: parseFloat(n.fob) || 1,
        landed: parseFloat(n.landed) || Math.round(parseFloat(n.fob || 1) * 9 * 100) / 100,
        preco: parseFloat(n.preco) || parseFloat(n.fob || 1) * 12,
        conc: n.concorrencia || n.conc || '--',
        score,
        recomendacao: recomendacaoFinal,
        regulacao: n.regulacao || n.certificacao || 'verificar',
        volume: parseFloat(n.volume_m3) || 0.01,
        modal: n.decisao_modal || 'LCL',
        categoria: category,
        ts: Date.now(),
        // Truth Engine fields (ProspecçãoPro-inspired)
        truth,
        truthLabel: truthLabels[truth],
        evidence: {
          source: 'deepseek-estimate',
          confidence: confiancaIA,
          generatedAt: new Date().toISOString(),
          method: 'ai_generated',
          fieldsObserved: ['name', 'ncm', 'fob', 'score', 'concorrencia']
        }
      };
    });

    // Calcular margem real
    nichos.forEach(n => {
      n.margem = n.preco > 0 ? Math.round((1 - (n.landed / n.preco)) * 100) / 100 : 0;
    });

    // Iron Rules alerts
    const alerts = [];
    nichos.forEach(n => {
      if (n.regulacao && n.regulacao !== 'nenhuma' && n.regulacao !== 'verificar') {
        alerts.push(`⚠️ ${n.nome}: exige ${n.regulacao} — verificar prazos e custos antes de importar`);
      }
      if (n.margem < 0.20) {
        alerts.push(`⚠️ ${n.nome}: margem < 20% — considere kit ou negocie FOB`);
      }
      if (n.volume > 5) {
        alerts.push(`📦 ${n.nome}: volume alto (${n.volume}m³) — verifique viabilidade logística`);
      }
    });

    return res.status(200).json({
      categoria: category,
      nichos,
      total: nichos.length,
      go: nichos.filter(n => n.score >= 70).length,
      top: nichos.filter(n => n.score >= 85).length,
      alerts: alerts.slice(0, 5),
      methodology: 'china-brazil-import-strategy v1.0',
      ts: new Date().toISOString(),
    });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
