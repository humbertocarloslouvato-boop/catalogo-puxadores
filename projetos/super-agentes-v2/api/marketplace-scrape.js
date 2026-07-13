// Scraping híbrido dos marketplaces brasileiros
// Estratégia: 1) Tentar scraping real, 2) Se falhar, usar IA com conhecimento de mercado
// POST /api/marketplace-scrape { product, marketplaces[], api_key }

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const { product, marketplaces, api_key } = req.body || {};
  if (!product) return res.status(400).json({ error: 'product obrigatório' });

  const results = {};
  const scraped = { success: [], blocked: [], failed: [], ai: [] };

  try {
    // 1. MERCADO LIVRE - API pública
    if (!marketplaces || marketplaces.includes('mercadolivre')) {
      try {
        const mlUrl = `https://api.mercadolibre.com/sites/MLB/search?q=${encodeURIComponent(product)}&limit=10`;
        const mlRes = await fetch(mlUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
          }
        });
        
        if (mlRes.ok) {
          const mlData = await mlRes.json();
          const precos = mlData.results.map(r => r.price).filter(p => p > 0);
          precos.sort((a, b) => a - b);
          
          results.mercadolivre = {
            source: 'real-scraping',
            totalResults: mlData.paging.total,
            products: mlData.results.map(r => ({
              title: r.title,
              price: r.price,
              soldQuantity: r.sold_quantity,
              seller: r.seller.nickname,
              sellerReputation: r.seller.seller_reputation.level,
              freeShipping: r.shipping.free_shipping,
              full: r.shipping.tags.includes('fulfillment'),
              permalink: r.permalink,
            })),
            priceDistribution: precos.length > 0 ? {
              min: precos[0],
              max: precos[precos.length - 1],
              p25: precos[Math.floor(precos.length * 0.25)],
              p50: precos[Math.floor(precos.length * 0.5)],
              p75: precos[Math.floor(precos.length * 0.75)],
              p90: precos[Math.floor(precos.length * 0.9)],
            } : null,
            topSellers: mlData.results
              .filter(r => r.sold_quantity > 0)
              .sort((a, b) => b.sold_quantity - a.sold_quantity)
              .slice(0, 5)
              .map(r => ({
                name: r.seller.nickname,
                product: r.title,
                price: r.price,
                sold: r.sold_quantity,
                level: r.seller.seller_reputation.level,
              })),
          };
          scraped.success.push('mercadolivre');
        } else {
          scraped.failed.push('mercadolivre');
        }
      } catch (e) {
        scraped.failed.push('mercadolivre');
      }
    }

    // 2. SHOPEE - tentar scraping
    if (!marketplaces || marketplaces.includes('shopee')) {
      try {
        const shopeeUrl = `https://shopee.com.br/search?keyword=${encodeURIComponent(product)}`;
        const shopeeRes = await fetch(shopeeUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
          }
        });
        
        if (shopeeRes.ok) {
          const html = await shopeeRes.text();
          const match = html.match(/<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.+?});<\/script>/);
          if (match) {
            try {
              const data = JSON.parse(match[1]);
              if (data.items || data.search_results) {
                const items = data.items || data.search_results.items || [];
                results.shopee = {
                  source: 'real-scraping',
                  totalResults: items.length,
                  products: items.slice(0, 10).map(item => ({
                    title: item.name,
                    price: item.price / 100000,
                    sold: item.sold || 0,
                    shopId: item.shop_id,
                    shopName: item.shop_name,
                    rating: item.rating || 0,
                    likes: item.liked_count || 0,
                  })),
                };
                scraped.success.push('shopee');
              }
            } catch (e) {
              scraped.failed.push('shopee');
            }
          }
        }
        
        if (!results.shopee) {
          scraped.blocked.push('shopee');
        }
      } catch (e) {
        scraped.failed.push('shopee');
      }
    }

    // 3. AMAZON - tentar scraping
    if (!marketplaces || marketplaces.includes('amazon')) {
      try {
        const amazonUrl = `https://www.amazon.com.br/s?k=${encodeURIComponent(product)}`;
        const amazonRes = await fetch(amazonUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9',
          }
        });
        
        if (amazonRes.ok) {
          const html = await amazonRes.text();
          const products = [];
          const regex = /data-component-type="s-search-result"[^>]*>[\s\S]*?<span class="a-price">[\s\S]*?<span class="a-offscreen">R\$&nbsp;([\d,.]+)<\/span>[\s\S]*?<span class="a-text-normal">([^<]+)<\/span>[\s\S]*?<span class="a-size-base">(\d+)[\s\S]*?avaliações?<\/span>/g;
          let match;
          while ((match = regex.exec(html)) !== null && products.length < 10) {
            products.push({
              price: parseFloat(match[1].replace(/\./g, '').replace(',', '.')),
              title: match[2].trim(),
              reviews: parseInt(match[3]),
            });
          }
          
          if (products.length > 0) {
            const precos = products.map(p => p.price).sort((a, b) => a - b);
            results.amazon = {
              source: 'real-scraping',
              totalResults: products.length,
              products,
              priceDistribution: {
                min: precos[0],
                max: precos[precos.length - 1],
                p25: precos[Math.floor(precos.length * 0.25)],
                p50: precos[Math.floor(precos.length * 0.5)],
                p75: precos[Math.floor(precos.length * 0.75)],
                p90: precos[Math.floor(precos.length * 0.9)],
              },
            };
            scraped.success.push('amazon');
          } else {
            scraped.blocked.push('amazon');
          }
        }
      } catch (e) {
        scraped.failed.push('amazon');
      }
    }

    // 4. MAGALU e TIKTOK - marcar como bloqueados
    if (!marketplaces || marketplaces.includes('magalu')) {
      scraped.blocked.push('magalu');
    }
    if (!marketplaces || marketplaces.includes('tiktok')) {
      scraped.blocked.push('tiktok');
    }

    // FALLBACK: Se nenhum marketplace retornou dados e temos api_key, usar IA
    if (scraped.success.length === 0 && api_key) {
      try {
        const aiUrl = 'https://api.deepseek.com/v1/chat/completions';
        const aiRes = await fetch(aiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${api_key}`,
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: [
              {
                role: 'system',
                content: `Você é um analista de mercado brasileiro com conhecimento atualizado sobre e-commerce. 
                Quando perguntado sobre um produto, forneça estimativas realistas baseadas em seu conhecimento de mercado.
                Retorne APENAS JSON válido, sem markdown.`
              },
              {
                role: 'user',
                content: `Analise o mercado brasileiro para "${product}" nos marketplaces (Mercado Livre, Shopee, Amazon, Magalu, TikTok Shop).
                
                Forneça estimativas realistas para cada marketplace:
                - totalResults: número estimado de produtos
                - priceRange: { min, max, p25, p50, p75, p90 } em R$
                - topSellers: array com até 5 vendedores (name, shopName, estimatedSales, rating)
                - insights: array com 3-5 insights sobre o mercado
                
                Retorne JSON no formato:
                {
                  "mercadolivre": { source: "ai-estimate", totalResults: X, priceDistribution: {...}, topSellers: [...] },
                  "shopee": { source: "ai-estimate", ... },
                  "amazon": { source: "ai-estimate", ... },
                  "insights": ["...", "...", "..."]
                }`
              }
            ],
            temperature: 0.7,
            max_tokens: 2000,
          }),
        });

        if (aiRes.ok) {
          const aiData = await aiRes.json();
          const content = aiData.choices?.[0]?.message?.content || '';
          
          const jsonMatch = content.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const aiAnalysis = JSON.parse(jsonMatch[0]);
            
            // Usar dados da IA apenas para marketplaces que falharam
            if (aiAnalysis.mercadolivre && scraped.failed.includes('mercadolivre')) {
              results.mercadolivre = { ...aiAnalysis.mercadolivre, source: 'ai-estimate' };
            }
            if (aiAnalysis.shopee && scraped.failed.includes('shopee')) {
              results.shopee = { ...aiAnalysis.shopee, source: 'ai-estimate' };
            }
            if (aiAnalysis.amazon && scraped.failed.includes('amazon')) {
              results.amazon = { ...aiAnalysis.amazon, source: 'ai-estimate' };
            }
            
            results.insights = aiAnalysis.insights || [];
            scraped.ai.push('deepseek');
          }
        }
      } catch (err) {
        console.warn('Erro no fallback IA:', err);
      }
    } else if (scraped.success.length === 0 && !api_key) {
      // Sem scraping bem-sucedido E sem API key
      return res.status(503).json({
        error: 'Não foi possível obter dados dos marketplaces',
        details: 'Configure uma chave de API em ⚙️ IA para análise via IA',
        marketplaces_failed: scraped.failed,
        marketplaces_blocked: scraped.blocked
      });
    }

    return res.status(200).json({
      product,
      timestamp: new Date().toISOString(),
      results,
      summary: {
        marketplacesScraped: Object.keys(results).length,
        marketplacesWithData: Object.values(results).filter(r => !r.error && !r.blocked).length,
        marketplacesBlocked: Object.values(results).filter(r => r.blocked).length,
        marketplacesError: Object.values(results).filter(r => r.error).length,
      }
    });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
