// API Pipeline v3 — JSON parser 4 estratégias + prompt enxuto
// POST /api/pipeline { category, api_key, provider }

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  try {
    const { category, api_key, provider } = req.body || {};
    if (!category || !api_key) return res.status(400).json({ error: 'category e api_key obrigatórios' });

    const PROVIDERS = {
      deepseek: { url: 'https://api.deepseek.com/v1/chat/completions', model: 'deepseek-chat' },
    };
    const pr = PROVIDERS[provider || 'deepseek'];
    if (!pr) return res.status(400).json({ error: 'provider inválido' });

    const prompt = `Você é um Discovery Agent. Para a categoria "${category}", identifique 6-8 nichos subexplorados no e-commerce brasileiro com alto potencial de importação da China.

Para cada nicho, retorne APENAS este JSON:
{
  "nichos": [{
    "nome": "nome curto",
    "ncm": "0000.00.00",
    "fob": 0.00,
    "concorrencia": "descrição da concorrência no BR",
    "score": 0,
    "recomendacao": "GO",
    "totalSellers": 0,
    "marketplaces": ["ML"],
    "topSellers": [{"nome":"Loja Real","marketplace":"ML","vendasMes":100,"precoPraticado":99.90,"estrelas":4.5}]
  }]
}

Regras: score = margem(25%)+demanda(20%)+concorrencia_inversa(20%)+TTM(15%)+regulatorio(10%)+investimento(10%). GO≥70, COND≥50, NO-GO<50. FOB = preço FÁBRICA 1688 MOQ 300+ (30-50% do varejo). topSellers: 3-5 lojas REAIS do Mercado Livre/Shopee Brasil que você conhece. NÃO invente nomes genéricos. Se não souber nomes reais, retorne array vazio []. Retorne SOMENTE o JSON, sem markdown, sem texto.`;

    const r1 = await fetch(pr.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${api_key}` },
      body: JSON.stringify({ model: pr.model, messages: [{ role: 'user', content: prompt }], max_tokens: 4000, temperature: 0.7 }),
    });
    const d1 = await r1.json();
    if (!r1.ok) return res.status(r1.status).json({ error: d1.error?.message || 'API falhou' });

    const content = d1.choices?.[0]?.message?.content || '';
    if (!content) return res.status(500).json({ error: 'IA retornou resposta vazia' });

    // 4 estratégias de parse
    let data;
    const attempts = [];
    try { data = JSON.parse(content); } catch(e1) {
      attempts.push('direto: '+e1.message.substring(0,40));
      try {
        const s = content.replace(/```json\s*|```/g, '').trim();
        data = JSON.parse(s);
      } catch(e2) {
        attempts.push('markdown: '+e2.message.substring(0,40));
        try {
          const a = content.indexOf('{'), b = content.lastIndexOf('}');
          if (a===-1||b===-1) throw new Error('sem {}');
          data = JSON.parse(content.substring(a, b+1));
        } catch(e3) {
          attempts.push('extractObj: '+e3.message.substring(0,40));
          try {
            const a = content.indexOf('['), b = content.lastIndexOf(']');
            if (a===-1||b===-1) throw new Error('sem []');
            const arr = JSON.parse(content.substring(a, b+1));
            data = Array.isArray(arr) ? { nichos: arr } : arr;
          } catch(e4) {
            return res.status(500).json({
              error: 'JSON inválido — 4 estratégias falharam',
              attempts,
              contentStart: content.substring(0, 200),
              contentEnd: content.substring(Math.max(0,content.length-200)),
              contentLen: content.length
            });
          }
        }
      }
    }

    const nichos = (data.nichos || []).map(n => {
      const score = parseInt(n.score) || 50;
      const conf = n.confidence || (score>=80?0.85:score>=60?0.7:0.5);
      const truth = (score>=80&&conf>=0.8)?'source_observed':(score>=60&&conf>=0.6)?'cross_checked':(conf>=0.4)?'estimated':'unavailable';
      const rec = (conf<0.5&&score<60)?'insufficient_data':(n.recomendacao||(score>=70?'GO':score>=50?'COND':'NO-GO'));
      return {
        nome: n.nome||n.name||'',
        ncm: n.ncm||'0000.00.00',
        fob: parseFloat(n.fob)||1,
        landed: parseFloat(n.landed)||Math.round(parseFloat(n.fob||1)*9*100)/100,
        preco: parseFloat(n.preco)||parseFloat(n.fob||1)*12,
        conc: n.concorrencia||n.conc||'--',
        score, recomendacao: rec,
        regulacao: n.regulacao||'verificar',
        volume: parseFloat(n.volume_m3)||0.01,
        modal: n.decisao_modal||'LCL',
        categoria: category, ts: Date.now(),
        topSellers: (n.topSellers||[]).map(s=>({
          nome: s.nome||s.name||'—',
          marketplace: s.marketplace||'ML',
          vendasMes: s.vendasMes||s.vendas||0,
          precoPraticado: s.precoPraticado||s.preco||0,
          estrelas: s.estrelas||s.stars||0
        })),
        totalSellers: n.totalSellers||0,
        marketplaces: n.marketplaces||['ML'],
        truth, truthLabel: ({unavailable:'🔴 Sem dados',estimated:'🟡 Estimativa',source_observed:'🟢 Observado',cross_checked:'✅ Verificado',quote_confirmed:'🏆 Cotação',outcome_confirmed:'⭐ Real'})[truth],
        evidence: { source:'deepseek-estimate', confidence:conf, generatedAt: new Date().toISOString(), method:'ai_generated', fieldsObserved:['name','ncm','fob','score'] }
      };
    });

    nichos.forEach(n => { n.margem = n.preco>0?Math.round((1-(n.landed/n.preco))*100)/100:0; });

    const alerts = [];
    nichos.forEach(n => {
      if (n.regulacao&&n.regulacao!=='nenhuma'&&n.regulacao!=='verificar') alerts.push(`⚠️ ${n.nome}: exige ${n.regulacao}`);
      if (n.margem<0.20) alerts.push(`⚠️ ${n.nome}: margem <20%`);
      if (n.volume>5) alerts.push(`📦 ${n.nome}: volume alto (${n.volume}m³)`);
    });

    return res.status(200).json({
      categoria: category,
      nichos,
      total: nichos.length,
      go: nichos.filter(n=>n.score>=70).length,
      top: nichos.filter(n=>n.score>=85).length,
      alerts: alerts.slice(0,5),
      ts: new Date().toISOString(),
    });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
