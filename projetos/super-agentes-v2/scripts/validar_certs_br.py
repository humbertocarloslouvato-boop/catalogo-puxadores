#!/usr/bin/env python3
"""
validar_certs_br.py — Validador de Certificações para o Brasil
Conceito: CE ≠ INMETRO, FDA ≠ ANVISA. Certs internacionais NÃO substituem BR.
Portado do conceito do ProspecçãoPro (ZCode).
"""
import json, sys

# ============================================================
# MAPEAMENTO POR CATEGORIA
# ============================================================
CERTS_POR_CATEGORIA = {
    'eletronicos':        ['INMETRO', 'ANATEL'],
    'eletrodomesticos':   ['INMETRO'],
    'brinquedos':         ['INMETRO'],
    'alimentos':          ['ANVISA', 'MAPA'],
    'suplementos':        ['ANVISA'],
    'cosmeticos':         ['ANVISA'],
    'medicamentos':       ['ANVISA'],
    'moveis':             ['INMETRO'],  # se componentes elétricos
    'ferramentas':        ['INMETRO'],
    'equipamentos_medicos': ['ANVISA', 'INMETRO'],
    'telecom':            ['ANATEL'],
    'automotivo':         ['INMETRO'],
    'construcao':         ['INMETRO'],
    'textil':             ['INMETRO'],
}

CUSTO_ESTIMADO = {
    'INMETRO': {'valor_min': 15000, 'valor_max': 30000, 'tempo_meses': '3-6'},
    'ANVISA':  {'valor_min': 50000, 'valor_max': 100000, 'tempo_meses': '6-12'},
    'ANATEL':  {'valor_min': 20000, 'valor_max': 40000, 'tempo_meses': '4-8'},
    'MAPA':    {'valor_min': 5000, 'valor_max': 15000, 'tempo_meses': '3-6'},
}

# Certs internacionais que NÃO valem no Brasil
CERTS_INTERNACIONAIS = ['CE', 'FDA', 'RoHS', 'FCC', 'UL', 'CSA', 'CCC', 'KC', 'PSE']

def validar_certs(fornecedor: dict, categoria: str) -> dict:
    """
    Valida certificações do fornecedor para o Brasil.
    
    Args:
        fornecedor: {certifications: ['CE','ISO9001',...]}
        categoria: 'eletronicos'|'alimentos'|'suplementos'|...
    
    Returns:
        {valido, faltantes[], enganosas[], custo_total, tempo_total}
    """
    declaradas = fornecedor.get('certifications', [])
    necessarias = CERTS_POR_CATEGORIA.get(categoria, ['INMETRO'])  # default
    
    # Identificar certs enganosas (internacionais que não valem no BR)
    enganosas = [c for c in declaradas if c in CERTS_INTERNACIONAIS]
    
    # Certs que realmente valem no BR
    validas_br = [c for c in declaradas if c in necessarias]
    
    # Certs faltantes
    faltantes = [c for c in necessarias if c not in declaradas]
    
    # Calcular custo total
    custo_min = 0
    custo_max = 0
    tempos = []
    
    for cert in faltantes:
        info = CUSTO_ESTIMADO.get(cert, {'valor_min': 5000, 'valor_max': 20000, 'tempo_meses': '3-6'})
        custo_min += info['valor_min']
        custo_max += info['valor_max']
        tempos.append(info['tempo_meses'])
    
    # Montar avisos
    avisos = []
    
    if enganosas:
        nomes = ', '.join(enganosas)
        avisos.append(
            f'⚠️ {nomes} são certificações INTERNACIONAIS — '
            f'NÃO substituem {"/".join(necessarias)} no Brasil. '
            f'Sem {"/".join(necessarias)}, produto é BARRADO na alfândega.'
        )
    
    for cert in faltantes:
        info = CUSTO_ESTIMADO.get(cert, {})
        avisos.append(
            f'⛔ Falta {cert} — '
            f'custo estimado: R$ {info["valor_min"]:,}-{info["valor_max"]:,}, '
            f'prazo: {info["tempo_meses"]} meses'
        )
    
    valido = len(faltantes) == 0
    
    return {
        'valido': valido,
        'categoria': categoria,
        'certificacoes_necessarias': necessarias,
        'certificacoes_declaradas': declaradas,
        'validas_br': validas_br,
        'faltantes': faltantes,
        'enganosas_internacionais': enganosas,
        'custo_total_min': custo_min,
        'custo_total_max': custo_max,
        'tempo_estimado': ' + '.join(sorted(set(tempos))) + ' meses' if tempos else 'N/A',
        'avisos': avisos,
        'recomendacao': _recomend(valido, faltantes, enganosas)
    }

def _recomend(valido: bool, faltantes: list, enganosas: list) -> str:
    if valido:
        return '✅ Todas as certificações BR necessárias estão presentes. Prosseguir com importação.'
    
    partes = []
    if enganosas:
        partes.append(f'certificações internacionais ({", ".join(enganosas)}) não substituem as BR')
    if faltantes:
        partes.append(f'faltam {len(faltantes)} certificações ({", ".join(faltantes)})')
    
    return f'❌ Fornecedor NÃO está pronto para importar para o Brasil: ' + '; '.join(partes) + '.'

# ============================================================
# TESTES
# ============================================================

def test():
    # Teste 1: Eletrônico com CE mas sem INMETRO
    r = validar_certs(
        {'certifications': ['CE', 'RoHS', 'FCC']},
        'eletronicos'
    )
    assert r['valido'] == False
    assert 'INMETRO' in r['faltantes']
    assert 'ANATEL' in r['faltantes']
    assert len(r['enganosas_internacionais']) == 3
    assert r['custo_total_min'] > 30000
    print(f"✅ Eletrônico sem certs BR: {len(r['avisos'])} avisos, custo R${r['custo_total_min']:,}-{r['custo_total_max']:,}")
    
    # Teste 2: Fornecedor OK
    r = validar_certs(
        {'certifications': ['INMETRO', 'ANATEL', 'ISO9001']},
        'eletronicos'
    )
    assert r['valido'] == True
    assert len(r['faltantes']) == 0
    print(f"✅ Eletrônico com certs BR: válido!")
    
    # Teste 3: Alimentos
    r = validar_certs(
        {'certifications': ['FDA', 'ISO22000']},
        'alimentos'
    )
    assert 'FDA' in r['enganosas_internacionais']
    assert 'ANVISA' in r['faltantes']
    print(f"✅ Alimentos com FDA: {len(r['avisos'])} avisos")
    
    print("\n✅ Todos os testes passaram!")

if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
    elif len(sys.argv) > 2:
        fornecedor = json.loads(sys.argv[1])
        categoria = sys.argv[2]
        resultado = validar_certs(fornecedor, categoria)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        test()
