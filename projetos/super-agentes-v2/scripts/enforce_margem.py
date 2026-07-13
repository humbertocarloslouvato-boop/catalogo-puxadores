#!/usr/bin/env python3
"""
enforce_margem.py — Auditoria Dupla
Conceito: "se cálculo diz margem negativa, NUNCA marca GO 
independente do que a IA sugerir"
Matemática prevalece sobre opinião da IA
"""
import json, sys, os
from datetime import datetime
from pathlib import Path

# ============================================================
# REGRAS DE OURO
# ============================================================

def enforce_margem(calculo: dict, estimativa_ia: dict = None) -> dict:
    """
    Auditoria dupla: cálculo determinístico vs estimativa IA
    
    Args:
        calculo: resultado do simulador_cvff/landed_cost
        estimativa_ia: output do agente Financeiro (opcional)
    
    Returns:
        {badge: 'GO'|'COND'|'NO-GO', razao: str, alertas: list}
    """
    margem_calc = calculo.get('margem_liquida', calculo.get('net_margin', 0))
    margem_ia = estimativa_ia.get('margem', margem_calc) if estimativa_ia else margem_calc
    
    alertas = []
    
    # Regra 1: Margem negativa = NUNCA GO
    if margem_calc < 0:
        return {
            'badge': 'NO-GO',
            'razao': f'Margem líquida negativa ({margem_calc*100:.1f}%). Produto dá PREJUÍZO.',
            'margem_calculada': margem_calc,
            'margem_ia': margem_ia,
            'alertas': ['🔴 MARGEM NEGATIVA — pare imediatamente']
        }
    
    # Regra 2: Margem fina (< 20%)
    if margem_calc < 0.20:
        alertas.append(f'⚠️ Margem fina ({margem_calc*100:.1f}%). Risco elevado.')
    
    # Regra 3: Divergência IA vs cálculo (> 15pp)
    if estimativa_ia and abs(margem_calc - margem_ia) > 0.15:
        alertas.append(
            f'⚠️ Divergência IA vs cálculo: IA estimou {margem_ia*100:.1f}%, '
            f'cálculo real {margem_calc*100:.1f}% (diferença {abs(margem_calc-margem_ia)*100:.1f}pp)'
        )
    
    # Regra 4: CVFF come margem (ticket < R$80)
    preco = calculo.get('preco_venda', calculo.get('sell_price_brl', 0))
    cvff = calculo.get('cvff', 0)
    if preco < 80 and cvff > preco * 0.05:
        alertas.append(f'💡 CVFF (R${cvff:.2f}) come {cvff/preco*100:.1f}% do preço. Considere vender em KIT.')
    
    # Decisão final
    if margem_calc >= 0.30 and not alertas:
        return {
            'badge': 'GO',
            'razao': f'Margem saudável ({margem_calc*100:.1f}%). Sem alertas.',
            'margem_calculada': margem_calc,
            'margem_ia': margem_ia,
            'alertas': []
        }
    elif margem_calc >= 0.20:
        return {
            'badge': 'COND',
            'razao': f'Margem OK ({margem_calc*100:.1f}%) mas com ressalvas.',
            'margem_calculada': margem_calc,
            'margem_ia': margem_ia,
            'alertas': alertas
        }
    else:
        return {
            'badge': 'NO-GO',
            'razao': f'Margem insuficiente ({margem_calc*100:.1f}%). Não recomendado.',
            'margem_calculada': margem_calc,
            'margem_ia': margem_ia,
            'alertas': alertas
        }

# ============================================================
# TESTES
# ============================================================

def test():
    """Testes unitários"""
    # Teste 1: Margem negativa
    r = enforce_margem({'margem_liquida': -0.05, 'preco_venda': 100, 'cvff': 5})
    assert r['badge'] == 'NO-GO', f"Esperado NO-GO, obtido {r['badge']}"
    
    # Teste 2: Margem saudável
    r = enforce_margem({'margem_liquida': 0.35, 'preco_venda': 200, 'cvff': 5})
    assert r['badge'] == 'GO', f"Esperado GO, obtido {r['badge']}"
    
    # Teste 3: Margem fina com divergência IA
    r = enforce_margem(
        {'margem_liquida': 0.15, 'preco_venda': 50, 'cvff': 5.50},
        {'margem': 0.45}
    )
    assert r['badge'] == 'NO-GO', f"Margem 15% deveria ser NO-GO"
    assert len(r['alertas']) >= 2, "Deveria ter alerta de divergência + CVFF"
    
    # Teste 4: CVFF come margem
    r = enforce_margem({'margem_liquida': 0.25, 'preco_venda': 30, 'cvff': 5.50})
    assert any('KIT' in a for a in r['alertas']), "Deveria sugerir KIT"
    
    print("✅ Todos os testes passaram!")

if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
    elif len(sys.argv) > 1:
        # Modo CLI: recebe JSON do cálculo
        entrada = json.loads(sys.argv[1])
        resultado = enforce_margem(entrada.get('calculo', entrada))
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        # Modo interativo
        test()
        print("\nUso: python enforce_margem.py '{\"calculo\":{\"margem_liquida\":0.32}}'")
