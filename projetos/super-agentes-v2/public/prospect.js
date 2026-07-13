// Prospecção - Gerenciamento de nichos e ranking
import { TEIA } from './teia.js';

export const DADOS_NICHOS = {
  'bebedouro pet': { ncm: '8421.21.00', fob: 8.00, landed: 17.25, preco: 89.90, margem: 0.32, conc: 6, score: 72 },
  'fonte água gato': { ncm: '8421.21.00', fob: 6.50, landed: 14.80, preco: 79.90, margem: 0.35, conc: 4, score: 78 },
  'arranhador sisal': { ncm: '4421.99.00', fob: 12.00, landed: 26.50, preco: 149.90, margem: 0.28, conc: 3, score: 85 },
  'coleira gps': { ncm: '8526.91.00', fob: 15.00, landed: 42.00, preco: 199.90, margem: 0.25, conc: 2, score: 88 },
};

export const CATEGORIAS = {
  '🐱 Pet': ['bebedouro pet', 'fonte água gato', 'arranhador sisal', 'coleira gps', 'cama pet'],
  '🏠 Casa': ['organizador', 'puxador inox', 'luminária led', 'prateleira', 'tapete'],
  '💪 Fitness': ['faixa elástica', 'halter', 'tapete yoga', 'corda pular', 'rolo espuma'],
  '👶 Baby': ['mordedor silicone', 'babador', 'tapete emborrachado', 'organizador', 'brinquedo'],
  '🔌 Eletrônicos': ['carregador rápido', 'cabo usb-c', 'fone bluetooth', 'suporte celular', 'power bank']
};

export function gerarRanking(nichos, categoria) {
  const resultados = nichos.map(nome => {
    const dados = DADOS_NICHOS[nome] || gerarNichoAleatorio(nome);
    return { nome, ...dados, categoria };
  });
  
  return resultados.sort((a, b) => b.score - a.score);
}

function gerarNichoAleatorio(nome) {
  const fob = Math.random() * 20 + 5;
  const landed = fob * 2.2;
  const preco = landed * 2.5;
  const margem = (preco - landed) / preco;
  const conc = Math.floor(Math.random() * 15) + 1;
  const score = Math.floor(margem * 100 - conc * 2);
  
  return {
    ncm: '0000.00.00',
    fob: fob.toFixed(2),
    landed: landed.toFixed(2),
    preco: preco.toFixed(2),
    margem: margem.toFixed(2),
    conc,
    score: Math.max(0, Math.min(100, score))
  };
}

export function filtrarRanking(categoria) {
  return TEIA.dados.ranking.filter(item => 
    categoria === 'Todas' || item.categoria === categoria
  );
}

export function atualizarRanking(novosNichos) {
  TEIA.dados.ranking = novosNichos;
}
