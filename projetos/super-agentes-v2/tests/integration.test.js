// Testes de integração - Smoke tests
// Rodar: node tests/integration.test.js

import { test } from 'node:test';
import assert from 'node:assert';
import { readFile } from 'node:fs/promises';

test('index.html existe e é válido', async () => {
  const html = await readFile('index.html', 'utf-8');
  
  assert.ok(html.includes('<!DOCTYPE html>'));
  assert.ok(html.includes('<title>'));
  assert.ok(html.includes('teia.js'));
  assert.ok(html.includes('calculos.js'));
  assert.ok(html.includes('prospect.js'));
});

test('package.json tem type: module', async () => {
  const pkg = JSON.parse(await readFile('package.json', 'utf-8'));
  assert.strictEqual(pkg.type, 'module');
});

test('modulos podem ser importados', async () => {
  const { calcularCVFF } = await import('../public/calculos.js');
  const { TEIA } = await import('../public/teia.js');
  const { gerarRanking } = await import('../public/prospect.js');
  
  assert.strictEqual(typeof calcularCVFF, 'function');
  assert.ok(TEIA);
  assert.strictEqual(typeof gerarRanking, 'function');
});

test('API pipeline.js existe', async () => {
  const code = await readFile('api/pipeline.js', 'utf-8');
  
  assert.ok(code.includes('export default'));
  assert.ok(code.includes('max_tokens: 4000'));
  assert.ok(code.includes('4 estratégias'));
});

test('API ml-scraper.js existe', async () => {
  const code = await readFile('api/ml-scraper.js', 'utf-8');
  
  assert.ok(code.includes('export default'));
  assert.ok(code.includes('fetch'));
});

test('API proxy.js existe', async () => {
  const code = await readFile('api/proxy.js', 'utf-8');
  
  assert.ok(code.includes('export default'));
  assert.ok(code.includes('fetch'));
});

test('API state.js existe', async () => {
  const code = await readFile('api/state.js', 'utf-8');
  
  assert.ok(code.includes('export default'));
  assert.ok(code.includes('json'));
});
