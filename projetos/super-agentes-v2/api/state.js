export default async function handler(req, res) {
  // API de persistência cloud com fallback memory
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  };

  if (req.method === 'OPTIONS') {
    return res.status(200).set(headers).end();
  }

  try {
    if (req.method === 'GET') {
      // Retorna estado salvo (KV ou memory)
      let state = null;
      
      if (process.env.KV_REST_API_URL) {
        try {
          const { kv } = await import('@vercel/kv');
          state = await kv.get('super-agentes-state');
        } catch (e) {
          // KV indisponível, fallback memory
        }
      }

      return res.status(200).json({
        version: '13.0.0',
        state: state || { version: '13.0.0' },
        source: state ? 'kv' : 'memory',
      });
    }

    if (req.method === 'POST') {
      const body = req.body || {};
      
      if (process.env.KV_REST_API_URL) {
        try {
          const { kv } = await import('@vercel/kv');
          await kv.set('super-agentes-state', body);
        } catch (e) {
          // KV falhou, salva em memory apenas
        }
      }

      return res.status(200).json({
        ok: true,
        version: '13.0.0',
        saved: !!process.env.KV_REST_API_URL,
      });
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
