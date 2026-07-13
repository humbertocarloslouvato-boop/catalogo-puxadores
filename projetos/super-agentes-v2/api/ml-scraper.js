// ML Scraper REAL — Scraping direto da página HTML do Mercado Livre
import { load } from 'cheerio';

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });

  const q = (req.query.q || '').trim();
  if (!q) return res.status(400).json({ error: 'Parâmetro q obrigatório' });

  try {
    const limit = Math.min(parseInt(req.query.limit) || 10, 20);

    // Scraping direto da página de busca do ML
    const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(q)}#D[A:${encodeURIComponent(q)}]`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
      },
      redirect: 'follow',
    });

    if (!response.ok) {
      return res.status(response.status).json({ 
        error: `ML retornou ${response.status}`,
        url 
      });
    }

    const html = await response.text();
    const $ = load(html);

    // Extrair produtos da página
    const products = [];
    const results = $('.ui-search-layout__item, .ui-search-result__wrapper, .andes-card');
    
    results.slice(0, limit).each((i, el) => {
      const $el = $(el);
      
      // Preço
      const priceText = $el.find('.andes-money-amount__fraction').first().text().trim();
      const price = parseFloat(priceText.replace(/\./g, '').replace(',', '.'));
      
      // Título
      const title = $el.find('.ui-search-item__title, .ui-search-card__title').first().text().trim();
      
      // Vendedor
      const seller = $el.find('.ui-search-item__group__element .ui-search-store-info__title, .ui-search-item__seller').first().text().trim();
      
      // Quantidade vendida
      const soldText = $el.find('.ui-search-item__group__element .ui-search-label, .ui-search-card__subtitles').text();
      const soldMatch = soldText.match(/(\d+)\s*vendidos/i);
      const sold = soldMatch ? parseInt(soldMatch[1]) : 0;
      
      // Link
      const link = $el.find('a.ui-search-link').first().attr('href') || $el.find('a').first().attr('href') || '';
      
      // Imagem
      const image = $el.find('img').first().attr('data-src') || $el.find('img').first().attr('src') || '';
      
      // Frete grátis
      const freeShipping = $el.text().toLowerCase().includes('frete grátis') || $el.text().toLowerCase().includes('frete gratis');
      
      // Full (fulfillment)
      const isFull = $el.text().toLowerCase().includes('full');

      if (title && price > 0) {
        products.push({
          titulo: title,
          preco: price,
          vendedor: seller || '—',
          vendidos: sold,
          frete_gratis: freeShipping,
          full: isFull,
          link: link,
          imagem: image,
          marketplace: 'ML',
        });
      }
    });

    // Calcular estatísticas
    const precos = products.map(p => p.preco).filter(p => p > 0);
    precos.sort((a, b) => a - b);
    
    const stats = precos.length > 0 ? {
      total: precos.length,
      min: precos[0],
      max: precos[precos.length - 1],
      media: precos.reduce((a, b) => a + b, 0) / precos.length,
      mediana: precos[Math.floor(precos.length / 2)],
      p25: precos[Math.floor(precos.length * 0.25)],
      p75: precos[Math.floor(precos.length * 0.75)],
      p90: precos[Math.floor(precos.length * 0.90)],
    } : null;

    // Top vendedores
    const vendedorMap = {};
    products.forEach(p => {
      if (p.vendedor && p.vendedor !== '—') {
        if (!vendedorMap[p.vendedor]) {
          vendedorMap[p.vendedor] = { nome: p.vendedor, produtos: 0, vendas: 0 };
        }
        vendedorMap[p.vendedor].produtos++;
        vendedorMap[p.vendedor].vendas += p.vendidos;
      }
    });
    const topVendedores = Object.values(vendedorMap)
      .sort((a, b) => b.vendas - a.vendas)
      .slice(0, 5);

    return res.status(200).json({
      query: q,
      url,
      total: products.length,
      products,
      stats,
      topVendedores,
      source: 'mercadolibre_html_scraping',
      retrievedAt: new Date().toISOString(),
    });

  } catch (e) {
    console.error('ML Scraper error:', e);
    return res.status(500).json({ error: e.message });
  }
}
