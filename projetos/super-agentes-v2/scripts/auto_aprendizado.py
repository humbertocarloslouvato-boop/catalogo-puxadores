#!/usr/bin/env python3
"""
auto_aprendizado.py — TEIA + LEARNER
Sistema de auto-aprendizado contínuo: registra projeções, 
compara com realidade, recalibra fatores de correção.
"""
import json, sys, os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / 'projetos' / 'super-agentes-v2' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LEARNER
# ============================================================

class Learner:
    """Sistema de auto-aprendizado com calibração por outcome"""
    
    def __init__(self):
        self.state_file = DATA_DIR / 'learner_state.json'
        self.state = self._load()
    
    def _load(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            'projecoes': [],           # histórico de projeções
            'outcomes': [],            # resultados reais
            'vieses': {},              # viés por dimensão
            'confianca': 0.5,          # nível de confiança (0-1)
            'amostras': 0,             # total de amostras
            'criado_em': datetime.now().isoformat(),
        }
    
    def _save(self):
        self.state_file.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))
    
    def registrar_projecao(self, produto, categoria, ncm, margem_projetada, preco, fob=None):
        """Registra uma projeção antes da venda real"""
        proj = {
            'produto': produto,
            'categoria': categoria,
            'ncm': ncm,
            'margem_projetada': margem_projetada,
            'preco': preco,
            'fob': fob,
            'data_projecao': datetime.now().isoformat(),
            'status': 'pendente'  # aguardando resultado real
        }
        self.state['projecoes'].append(proj)
        self._save()
        return len(self.state['projecoes']) - 1  # índice
    
    def registrar_outcome(self, indice, margem_real, feedback=''):
        """Registra o resultado real e recalibra"""
        if indice >= len(self.state['projecoes']):
            raise ValueError(f'Índice {indice} inválido. Total: {len(self.state["projecoes"])}')
        
        proj = self.state['projecoes'][indice]
        proj['margem_real'] = margem_real
        proj['status'] = 'concluido'
        proj['feedback'] = feedback
        
        # Classificar outcome
        erro = proj['margem_projetada'] - margem_real
        if abs(erro) < 0.05:
            proj['resultado'] = 'acertou'
        elif erro > 0:
            proj['resultado'] = 'errou_alta'  # projeção foi otimista demais
        else:
            proj['resultado'] = 'errou_baixa'  # projeção foi pessimista
        
        # Registrar para calibração
        self.state['outcomes'].append({
            'produto': proj['produto'],
            'categoria': proj['categoria'],
            'ncm': proj['ncm'],
            'margem_projetada': proj['margem_projetada'],
            'margem_real': margem_real,
            'erro': erro,
            'resultado': proj['resultado'],
        })
        
        # Recalibrar viés
        self._recalibrar()
        self._save()
        
        return proj
    
    def _recalibrar(self):
        """Recalibra vieses por dimensão"""
        outcomes = self.state['outcomes']
        if not outcomes:
            return
        
        # Viés global
        erros = [o['erro'] for o in outcomes]
        vies_global = sum(erros) / len(erros)
        
        # Viés por categoria
        vieses_cat = {}
        for o in outcomes:
            cat = o['categoria']
            if cat not in vieses_cat:
                vieses_cat[cat] = []
            vieses_cat[cat].append(o['erro'])
        
        # Precisão (% dentro de ±5pp)
        acertos = sum(1 for o in outcomes if abs(o['erro']) < 0.05)
        precisao = acertos / len(outcomes)
        
        self.state['vieses'] = {
            'global': round(vies_global, 4),
            'por_categoria': {cat: round(sum(e)/len(e), 4) for cat, e in vieses_cat.items()},
        }
        self.state['confianca'] = round(precisao, 4)
        self.state['amostras'] = len(outcomes)
    
    def calibrar_margem(self, margem_projetada, categoria):
        """Aplica calibração a uma nova projeção"""
        vies = self.state['vieses'].get('por_categoria', {}).get(categoria, 0)
        if vies == 0:
            vies = self.state['vieses'].get('global', 0)
        
        margem_calibrada = margem_projetada - vies
        return {
            'margem_original': margem_projetada,
            'margem_calibrada': round(margem_calibrada, 4),
            'vies_aplicado': round(vies, 4),
            'confianca': self.state['confianca'],
            'amostras': self.state['amostras'],
        }
    
    def status(self):
        """Retorna status do learner"""
        return {
            'projecoes_pendentes': sum(1 for p in self.state['projecoes'] if p['status'] == 'pendente'),
            'projecoes_concluidas': sum(1 for p in self.state['projecoes'] if p['status'] == 'concluido'),
            'outcomes': self.state['amostras'],
            'confianca': f"{self.state['confianca']*100:.1f}%",
            'vies_global': f"{self.state['vieses'].get('global', 0)*100:+.1f}pp",
        }

# ============================================================
# TEIA — Event Bus
# ============================================================

class TEIA:
    """Ecossistema de interconexão entre módulos"""
    
    def __init__(self):
        self.log_file = DATA_DIR / 'teia_log.json'
        self.pulse = {'ciclos': 0, 'calculos': 0, 'prospeccoes': 0, 'consultas': 0}
        self._load_log()
    
    def _load_log(self):
        if self.log_file.exists():
            self.log = json.loads(self.log_file.read_text())
        else:
            self.log = []
    
    def registrar(self, acao, dados=None):
        """Registra ação no ecossistema"""
        self.pulse['ciclos'] += 1
        
        if 'calculo' in acao: self.pulse['calculos'] += 1
        if 'prosp' in acao: self.pulse['prospeccoes'] += 1
        if 'consulta' in acao: self.pulse['consultas'] += 1
        
        evento = {
            'acao': acao,
            'ts': datetime.now().isoformat(),
            'dados': dados or {},
        }
        self.log.append(evento)
        
        # Manter últimos 100 eventos
        if len(self.log) > 100:
            self.log = self.log[-100:]
        
        self.log_file.write_text(json.dumps(self.log, indent=2, ensure_ascii=False))
        
        # Retornar sugestões contextuais
        return self._trigger(acao, dados or {})
    
    def _trigger(self, acao, dados):
        """Gera sugestões contextuais baseadas na ação"""
        sugestoes = []
        preco = dados.get('preco_venda', dados.get('preco', 0))
        margem = dados.get('margem_liquida', dados.get('margem', 0))
        
        if preco > 0 and preco < 80:
            sugestoes.append({
                'skill': 'bundle_optimizer',
                'msg': f'💡 CVFF come margem — venda em KIT (preço R${preco:.2f} < R$80)',
                'target': 'calc'
            })
        
        if margem > 0.50:
            sugestoes.append({
                'skill': 'elasticidade_preco',
                'msg': f'📈 Margem alta ({margem*100:.0f}%) — teste preço premium',
                'target': 'calc'
            })
        
        if margem < 0.15 and margem > 0:
            sugestoes.append({
                'skill': 'fornecedor_china',
                'msg': f'⚠️ Margem apertada ({margem*100:.0f}%) — negocie FOB na China',
                'target': 'forn'
            })
        
        return sugestoes
    
    def status(self):
        return {
            'pulse': self.pulse,
            'total_eventos': len(self.log),
            'brain_level': '🌲' if self.pulse['ciclos'] > 100 else '🌿',
        }

# ============================================================
# TESTE
# ============================================================

def test():
    import tempfile
    # Usar diretório temporário para teste (evita conflito com dados reais)
    temp_dir = tempfile.mkdtemp(prefix='learner_test_')
    # Sobrescrever DATA_DIR para o Learner
    import auto_aprendizado
    auto_aprendizado.DATA_DIR = Path(temp_dir) / 'data'
    auto_aprendizado.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Testar Learner
    learner = auto_aprendizado.Learner()
    idx = learner.registrar_projecao('Bebedouro Pet', 'pet', '8421.21.00', 0.32, 159.90, 8.00)
    assert idx == 0
    
    result = learner.registrar_outcome(0, 0.22, 'FOB subiu de $8 para $9')
    assert result['resultado'] == 'errou_alta'
    
    cal = learner.calibrar_margem(0.32, 'pet')
    assert cal['margem_calibrada'] < 0.32  # deve reduzir margem
    
    status = learner.status()
    assert status['outcomes'] == 1
    
    # Testar TEIA
    teia = auto_aprendizado.TEIA()
    sugs = teia.registrar('calculo_cvff', {'preco_venda': 36.40, 'margem_liquida': 0.055})
    assert len(sugs) > 0
    
    # Limpar temp
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print('✅ Todos os testes passaram!')
    print(f'   Learner: {status}')
    print(f'   TEIA: {teia.status()["pulse"]}')

if __name__ == '__main__':
    if '--test' in sys.argv:
        test()
    else:
        test()
