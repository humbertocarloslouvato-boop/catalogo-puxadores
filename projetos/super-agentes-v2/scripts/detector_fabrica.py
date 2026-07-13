#!/usr/bin/env python3
"""
detector_fabrica.py — Detector de Fábrica vs Trading Company
Score 0-100 com 8 sinais objetivos.
Portado do conceito do ProspecçãoPro (ZCode).
"""
import json, sys

# ============================================================
# SINAIS DE FÁBRICA REAL (usados via lookup direto nas keys)
# ============================================================
FACTORY_SIGNALS = {
    'ISO9001': 15,
    'ISO14001': 10,
    'BSCI': 10,
    'SGS_audited': 20,
    'TUV_audited': 20,
    'factory_assessment': 20,
}

def detectar_fabrica(fornecedor: dict) -> dict:
    """
    Detecta se fornecedor é fábrica real ou trading company.
    
    Args:
        fornecedor: {
            name, platform, certifications[], staff_count, 
            location, business_type, product_count, years_active,
            audit_type, has_machinery_photos, annual_revenue_usd
        }
    
    Returns:
        {verdict: 'FACTORY'|'UNCERTAIN'|'TRADING', confidence: 0-100, signals: []}
    """
    score = 50  # baseline neutra
    signals = []
    
    # === SINAIS POSITIVOS (FÁBRICA) ===
    certs = fornecedor.get('certifications', [])
    for cert in certs:
        if cert in FACTORY_SIGNALS:
            points = FACTORY_SIGNALS[cert]
            score += points
            signals.append(f'+{points} {cert}')
    
    # Audit type
    audit = fornecedor.get('audit_type', '')
    if audit in FACTORY_SIGNALS:
        points = FACTORY_SIGNALS[audit]
        score += points
        signals.append(f'+{points} {audit}')
    
    # Staff count
    staff = fornecedor.get('staff_count', 0)
    if staff > 200:
        score += 10
        signals.append('+10 staff>200')
    elif staff > 50:
        score += 5
        signals.append('+5 staff>50')
    
    # Catálogo focado (poucos produtos = fábrica especializada)
    products = fornecedor.get('product_count', 0)
    if products > 0 and products < 10:
        score += 10
        signals.append('+10 catálogo focado (<10)')
    
    # Anos de operação
    years = fornecedor.get('years_active', 0)
    if years > 10:
        score += 5
        signals.append('+5 anos>10')
    
    # Fotos de maquinário
    if fornecedor.get('has_machinery_photos'):
        score += 15
        signals.append('+15 fotos maquinário')
    
    # Receita anual
    revenue = fornecedor.get('annual_revenue_usd', 0)
    if revenue > 5_000_000:
        score += 5
        signals.append('+5 revenue>$5M')
    
    # === SINAIS NEGATIVOS (TRADING) ===
    # Localização Yiwu (hub de trading)
    location = fornecedor.get('location', '').lower()
    if 'yiwu' in location:
        score -= 20
        signals.append('-20 Yiwu (trading hub)')
    
    # Business type
    biz_type = fornecedor.get('business_type', '').lower()
    if 'trading' in biz_type:
        score -= 25
        signals.append('-25 trading company')
    
    # Catálogo muito amplo (>50 produtos)
    if products > 50:
        score -= 10
        signals.append('-10 catálogo amplo (>50)')
    
    # Resposta muito rápida (trading responde em minutos)
    response_hours = fornecedor.get('response_time_hours', 24)
    if response_hours < 4:
        score -= 5
        signals.append('-5 resposta rápida (<4h)')
    
    # === VEREDITO ===
    score = max(0, min(100, score))  # clamp 0-100
    
    if score > 70:
        verdict = 'FACTORY'
    elif score > 40:
        verdict = 'UNCERTAIN'
    else:
        verdict = 'TRADING'
    
    return {
        'verdict': verdict,
        'confidence': score,
        'signals': signals,
        'recommendation': _recommend(verdict, score)
    }

def _recommend(verdict: str, score: int) -> str:
    if verdict == 'FACTORY':
        return f'✅ Provável fábrica real (score {score}). Prosseguir com due diligence (SGS audit $250-400).'
    elif verdict == 'UNCERTAIN':
        return f'⚠️ Incerteza (score {score}). Solicitar factory audit + vídeo chamada de inspeção antes de fechar.'
    else:
        return f'🚨 Provável trading (score {score}). Adicionar 20-40% ao FOB estimado. Buscar em outras plataformas.'

# ============================================================
# TESTES
# ============================================================

def test():
    # Fábrica clara
    fab = detectar_fabrica({
        'name': 'Shenzhen Factory',
        'certifications': ['ISO9001', 'BSCI'],
        'staff_count': 300,
        'product_count': 5,
        'years_active': 12,
        'has_machinery_photos': True,
        'location': 'Shenzhen',
        'business_type': 'Manufacturer',
        'audit_type': 'SGS_audited',
        'annual_revenue_usd': 10_000_000,
        'response_time_hours': 24,
    })
    assert fab['verdict'] == 'FACTORY', f"Esperado FACTORY, obtido {fab['verdict']}"
    assert fab['confidence'] > 80, f"Score {fab['confidence']} deveria ser >80"
    print(f"✅ Fábrica: {fab['verdict']} (score {fab['confidence']})")
    
    # Trading clara
    trad = detectar_fabrica({
        'name': 'Yiwu Trading Co',
        'certifications': [],
        'staff_count': 10,
        'product_count': 200,
        'years_active': 2,
        'has_machinery_photos': False,
        'location': 'Yiwu, Zhejiang',
        'business_type': 'Trading Company',
        'audit_type': '',
        'annual_revenue_usd': 500_000,
        'response_time_hours': 1,
    })
    assert trad['verdict'] == 'TRADING', f"Esperado TRADING, obtido {trad['verdict']}"
    assert trad['confidence'] < 40, f"Score {trad['confidence']} deveria ser <40"
    print(f"✅ Trading: {trad['verdict']} (score {trad['confidence']})")
    
    print("\n✅ Todos os testes passaram!")

if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
    elif len(sys.argv) > 1:
        entrada = json.loads(sys.argv[1])
        resultado = detectar_fabrica(entrada)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        test()
