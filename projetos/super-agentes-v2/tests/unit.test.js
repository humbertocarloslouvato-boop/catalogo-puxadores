// Testes unitários para Super Agentes v2
// Rodar: node tests/unit.test.js

import { test } from 'node:test';
import assert from 'node:assert';
import { calcularCVFF, calcularMargem, calcularLandedCost } from '../public/calculos.js';
import { TEIA } from '../public/teia.js';
import { gerarRanking, DADOS_NICHOS } from '../public/prospect.js';

test('calcularCVFF - faixa 0-25', () => {
  assert.strictEqual(calcularCVFF(0), 4.50);
  assert.strictEqual(calcularCVFF(10), 4.50);
  assert.strictEqual(calcularCVFF(25), 4.50);
});

test('calcularCVFF - faixa 25-35', () => {
  assert.strictEqual(calcularCVFF(26), 5.00);
  assert.strictEqual(calcularCVFF(30), 5.00);
  assert.strictEqual(calcularCVFF(35), 5.00);
});

test('calcularCVFF - faixa 35-45', () => {
  assert.strictEqual(calcularCVFF(36), 5.50);
  assert.strictEqual(calcularCVFF(45), 5.50);
});

test('calcularCVFF - faixa 120+', () => {
  assert.strictEqual(calcularCVFF(121), 8.00);
  assert.strictEqual(calcularCVFF(500), 8.00);
});

test('calcularMargem - lucro positivo', () => {
  const margem = calcularMargem(10, 20, 50);
  assert.strictEqual(margem, 0.6); // (50-20)/50 = 0.6
});

test('calcularMargem - lucro zero', () => {
  const margem = calcularMargem(10, 50, 50);
  assert.strictEqual(margem, 0);
});

test('calcularMargem - prejuízo', () => {
  const margem = calcularMargem(10, 60, 50);
  assert.strictEqual(margem, -0.2); // (50-60)/50 = -0.2
});

test('calcularMargem - preço zero', () => {
  const margem = calcularMargem(10, 20, 0);
  assert.strictEqual(margem, 0); // proteção contra divisão por zero
});

test('calcularLandedCost - LCL padrão', () => {
  const result = calcularLandedCost(50, 'lcl', 0.01);
  
  assert.ok(result.cif);
  assert.ok(result.ii);
  assert.ok(result.ipi);
  assert.ok(result.pisCofins);
  assert.ok(result.icms);
  assert.ok(result.afrmm);
  assert.ok(result.landed);
  
  // Landed deve ser > CIF
  assert.ok(parseFloat(result.landed) > parseFloat(result.cif));
});

test('calcularLandedCost - aéreo', () => {
  const result = calcularLandedCost(50, 'aereo', 0.01);
  
  // Aéreo tem frete mais caro
  assert.ok(parseFloat(result.landed) > 100);
});

test('calcularLandedCost - FCL 20ft', () => {
  const result = calcularLandedCost(50, 'fcl20', 0.01);
  
  assert.ok(parseFloat(result.landed) > 0);
});

test('TEIA - registrar ação', () => {
  TEIA.reset();
  TEIA.registrar('calculo_cvff');
  
  const metrics = TEIA.getMetrics();
  assert.strictEqual(metrics.calculos, 1);
  assert.strictEqual(metrics.ciclos, 1);
  assert.strictEqual(metrics.historicoCount, 1);
});

test('TEIA - registrar múltiplas ações', () => {
  TEIA.reset();
  TEIA.registrar('calculo_cvff');
  TEIA.registrar('pipeline_ia');
  TEIA.registrar('consulta_ia');
  
  const metrics = TEIA.getMetrics();
  assert.strictEqual(metrics.calculos, 1);
  assert.strictEqual(metrics.prospecoes, 1);
  assert.strictEqual(metrics.consultas, 1);
  assert.strictEqual(metrics.ciclos, 3);
});

test('TEIA - sugestões automáticas', () => {
  TEIA.reset();
  TEIA.atualizarSugestoes();
  
  // Sem ações, deve sugerir pipeline
  assert.ok(TEIA.sugestoes.length > 0);
  assert.strictEqual(TEIA.sugestoes[0].tipo, 'info');
});

test('TEIA - historico não ultrapassa 100', () => {
  TEIA.reset();
  
  for (let i = 0; i < 150; i++) {
    TEIA.registrar('calculo_cvff');
  }
  
  const metrics = TEIA.getMetrics();
  assert.strictEqual(metrics.historicoCount, 100);
});

test('gerarRanking - com dados conhecidos', () => {
  const ranking = gerarRanking(['bebedouro pet', 'arranhador sisal'], 'Pet');
  
  assert.strictEqual(ranking.length, 2);
  assert.strictEqual(ranking[0].categoria, 'Pet');
  assert.ok(ranking[0].score >= ranking[1].score); // ordenado por score
});

test('gerarRanking - gerar nicho aleatório', () => {
  const ranking = gerarRanking(['produto novo'], 'Teste');
  
  assert.strictEqual(ranking.length, 1);
  assert.strictEqual(ranking[0].nome, 'produto novo');
  assert.ok(ranking[0].score >= 0 && ranking[0].score <= 100);
});

test('DADOS_NICHOS - estrutura válida', () => {
  const nicho = DADOS_NICHOS['bebedouro pet'];
  
  assert.ok(nicho.ncm);
  assert.ok(nicho.fob > 0);
  assert.ok(nicho.landed > 0);
  assert.ok(nicho.preco > 0);
  assert.ok(nicho.score >= 0 && nicho.score <= 100);
});
