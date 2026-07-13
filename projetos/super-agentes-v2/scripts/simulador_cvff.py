#!/usr/bin/env python3
"""
simulador_cvff.py — Simulador de CVFF com auditoria dupla integrada
Calcula margem líquida real no Mercado Livre com enforce_margem
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enforce_margem import enforce_margem

# Tabela oficial CVFF por faixa de preço
CVFF_TABLE = [
    (0, 25, 4.50),
    (25, 35, 5.00),
    (35, 45, 5.50),
    (45, 55, 6.00),
    (55, 70, 6.50),
    (70, 90, 7.00),
    (90, 120, 7.50),
    (120, float('inf'), 8.00),
]

def get_cvff(preco):
    """Retorna CVFF por faixa de preço"""
    for lo, hi, cvff in CVFF_TABLE:
        if lo < preco <= hi:
            return cvff
    return CVFF_TABLE[-1][2]

def simular_cvff(preco_venda, custo_unitario, tipo='classic', kit=1, embalagem=1.50):
    """
    Simula margem líquida no Mercado Livre com CVFF
    
    Args:
        preco_venda: preço de venda do produto/kit
        custo_unitario: custo unitário
        tipo: 'classic' (7%) ou 'premium' (12%)
        kit: quantidade de unidades no kit (1 = unitário)
        embalagem: custo de embalagem por unidade
    
    Returns:
        dict com detalhamento completo
    """
    preco_unitario = preco_venda / kit
    cvff = get_cvff(preco_venda)
    comissao_pct = 0.12 if tipo == 'premium' else 0.07
    comissao = preco_venda * comissao_pct
    
    receita = preco_venda
    custo_total = (custo_unitario + embalagem) * kit
    taxas = cvff + comissao
    
    lucro_liquido = receita - custo_total - taxas
    margem_liquida = lucro_liquido / receita if receita > 0 else 0
    
    resultado = {
        'preco_venda': preco_venda,
        'preco_unitario': preco_unitario,
        'custo_unitario': custo_unitario,
        'kit': kit,
        'tipo_anuncio': tipo,
        'cvff': cvff,
        'comissao_pct': comissao_pct * 100,
        'comissao': comissao,
        'embalagem_por_unidade': embalagem,
        'custo_total': custo_total,
        'taxas_total': taxas,
        'lucro_liquido': lucro_liquido,
        'margem_liquida': margem_liquida,
    }
    
    # Aplicar enforce (auditoria dupla)
    enforce = enforce_margem(resultado)
    resultado['enforce'] = enforce
    
    return resultado

def simular_cenarios(preco_venda, custo_unitario, kit=1):
    """Simula 4 cenários: classic kit x1, classic kit xN, premium kit x1, premium kit xN"""
    resultados = []
    
    for tipo in ['classic', 'premium']:
        for k in sorted(set([1, kit])):  # evita duplicata se kit=1
            if k == 1 and kit > 1:
                r = simular_cvff(preco_venda / kit, custo_unitario, tipo, 1)
            else:
                r = simular_cvff(preco_venda, custo_unitario, tipo, k)
            r['label'] = f'{tipo} / kit {k}un'
            resultados.append(r)
    
    return resultados

# ============================================================
# TESTE
# ============================================================
def test():
    r = simular_cvff(36.40, 2.89, kit=6)
    assert r['margem_liquida'] > 0, f"Margem negativa: {r['margem_liquida']}"
    assert 'enforce' in r
    
    # CVFF deve diluir em kit
    r_unit = simular_cvff(6.07, 2.89, 'classic', 1)
    r_kit = simular_cvff(36.40, 2.89, 'classic', 6)
    assert r_kit['margem_liquida'] > r_unit['margem_liquida'], "Kit deve melhorar margem"
    
    print('✅ Todos os testes passaram!')
    print(f'   Unitário: {r_unit["margem_liquida"]*100:.1f}% margem')
    print(f'   Kit 6un:   {r_kit["margem_liquida"]*100:.1f}% margem')

if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
    elif len(sys.argv) > 1:
        # Modo CLI: simular_cvff(preco, custo, tipo, kit)
        args = json.loads(sys.argv[1])
        r = simular_cvff(**args)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        test()
