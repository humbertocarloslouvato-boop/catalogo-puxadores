// API Proxy CORS para IAs
// Todas as chamadas de IA passam por aqui para evitar CORS
// Suporta: DeepSeek, Anthropic, MiniMax, Z.AI/GLM

const PROVIDERS = {
  deepseek: { url: 'https://api.deepseek.com/v1/chat/completions', model: 'deepseek-chat' },
  anthropic: { url: 'https://api.anthropic.com/v1/messages', model: 'claude-sonnet-4-20250514' },
  minimax: { url: 'https://api.minimax.chat/v1/text/chatcompletion_v2', model: 'MiniMax-Text-01' },
  zai: { url: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', model: 'glm-4' },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { provider, model, messages, max_tokens, api_key } = req.body || {};
    
    if (!provider || !messages || !api_key) {
      return res.status(400).json({ error: 'provider, messages e api_key são obrigatórios' });
    }

    const pr = PROVIDERS[provider];
    if (!pr) return res.status(400).json({ error: `Provider desconhecido: ${provider}` });

    const fetchOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model || pr.model,
        messages,
        max_tokens: max_tokens || 2000,
      }),
    };

    // Anthropic usa formato diferente: non-OpenAI-compatible
    if (provider === 'anthropic') {
      fetchOptions.body = JSON.stringify({
        model: model || pr.model,
        max_tokens: max_tokens || 2000,
        messages: messages,
      });
      fetchOptions.headers['x-api-key'] = api_key;
      fetchOptions.headers['anthropic-version'] = '2023-06-01';
    } else if (provider === 'zai') {
      fetchOptions.headers['Authorization'] = `Bearer ${api_key}`;
    } else {
      fetchOptions.headers['Authorization'] = `Bearer ${api_key}`;
    }

    const response = await fetch(pr.url, fetchOptions);
    let data;
    try {
      data = await response.json();
    } catch {
      return res.status(502).json({ error: 'Resposta inválida da API (não-JSON)' });
    }

    if (!response.ok) {
      return res.status(response.status).json({
        error: data.error?.message || `HTTP ${response.status}`,
        details: data
      });
    }

    // Normalizar resposta
    let content = '';
    if (provider === 'anthropic') {
      content = data.content?.[0]?.text || '';
    } else if (provider === 'zai') {
      content = data.choices?.[0]?.message?.content || '';
    } else {
      content = data.choices?.[0]?.message?.content || '';
    }

    return res.status(200).json({
      content,
      usage: data.usage || {},
      model: data.model || (model || pr.model),
    });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
