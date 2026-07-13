// API ML Scraper — Extrai dados REAIS de concorrentes do Mercado Livre Brasil
// GET /api/ml-scraper?q=bebedouro+pet&limit=5
// A API pública do ML é gratuita e sem autenticação

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });

  const q = (req.query.q || '').trim();
  if (!q) return res.status(400).json({ error: 'Parâmetro q obrigatório' });

  try {
    const limit = Math.min(parseInt(req.query.limit) || 5, 10);

    // API pública do Mercado Livre — sem auth, sem rate limit rígido
    const url = `https://api.mercadolibre.com/sites/MLB/search?q=${encodeURIComponent(q)}&limit=${limit}&sort=sold_quantity_desc`;

    const r = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9',
      }
    });
    if (!r.ok) return res.status(r.status).json({ error: 'ML API retornou ' + r.status });

    const data = await r.json();

    const sellers = (data.results || []).map(item => ({
      nome: item.seller?.nickname || '—',
      loja: item.seller?.seller_reputation?.power_seller_status || 'normal',
      titulo: item.title,
      preco: item.price,
      moeda: item.currency_id,
      vendidos: item.sold_quantity || 0,
      disponiveis: item.available_quantity || 0,
      avaliacoes: item.seller?.seller_reputation?.transactions?.total || 0,
      estrelas: parseFloat(item.seller?.seller_reputation?.transactions?.ratings?.positive || 0),
      envio_gratis: item.shipping?.free_shipping || false,
      full: item.shipping?.tags?.includes('fulfillment') || false,
      link: item.permalink,
      thumbnail: item.thumbnail,
      condicao: item.condition === 'new' ? 'Novo' : 'Usado',
      marketplace: 'ML',
    }));

    // Estatísticas agregadas
    const totalResults = data.paging?.total || 0;
    const precos = sellers.map(s => s.preco).filter(Boolean);
    const stats = precos.length > 0 ? {
      min: Math.min(...precos),
      max: Math.max(...precos),
      median: precos.sort((a,b) => a-b)[Math.floor(precos.length/2)],
      media: precos.reduce((a,b) => a+b, 0) / precos.length,
    } : null;

    return res.status(200).json({
      query: q,
      totalVendedores: totalResults,
      sellers,
      stats,
      source: 'mercadolibre_public_api',
      retrievedAt: new Date().toISOString(),
    });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
