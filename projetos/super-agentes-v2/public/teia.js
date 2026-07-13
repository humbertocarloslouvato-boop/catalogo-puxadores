// TEIA - Sistema de Estado Global
// Gerencia ranking, histórico, pulse e sugestões

export const TEIA = {
  dados: {
    ranking: [],
    historico: [],
    fornecedorAtual: null,
  },
  pulse: {
    ciclos: 0,
    calculos: 0,
    prospecoes: 0,
    consultas: 0,
  },
  sugestoes: [],
  
  registrar(acao) {
    this.pulse.ciclos++;
    if (acao === 'calculo_cvff') this.pulse.calculos++;
    if (acao === 'pipeline_ia') this.pulse.prospecoes++;
    if (acao === 'consulta_ia') this.pulse.consultas++;
    
    this.dados.historico.unshift({
      acao,
      timestamp: Date.now(),
    });
    
    if (this.dados.historico.length > 100) {
      this.dados.historico.pop();
    }
    
    this.atualizarSugestoes();
  },
  
  atualizarSugestoes() {
    this.sugestoes = [];
    
    if (this.pulse.prospecoes === 0) {
      this.sugestoes.push({
        tipo: 'info',
        msg: '💡 Execute o pipeline para descobrir nichos',
        target: 'pipeline'
      });
    }
    
    if (this.pulse.calculos === 0) {
      this.sugestoes.push({
        tipo: 'info',
        msg: '💡 Calcule CVFF para validar margens',
        target: 'cvff'
      });
    }
    
    if (this.dados.ranking.length === 0 && this.pulse.prospecoes > 0) {
      this.sugestoes.push({
        tipo: 'alert',
        msg: '⚠️ Pipeline executou mas nenhum nicho encontrado',
        target: 'pipeline'
      });
    }
  },
  
  getMetrics() {
    return {
      ...this.pulse,
      rankingCount: this.dados.ranking.length,
      historicoCount: this.dados.historico.length,
      sugestoesCount: this.sugestoes.length,
    };
  },
  
  reset() {
    this.pulse = { ciclos: 0, calculos: 0, prospecoes: 0, consultas: 0 };
    this.dados.historico = [];
    this.sugestoes = [];
  }
};
