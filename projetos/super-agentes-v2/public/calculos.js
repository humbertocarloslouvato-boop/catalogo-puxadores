// Cálculos de CVFF e Landed Cost
// Funções puras para testabilidade

export function calcularCVFF(preco) {
  if (preco <= 25) return 4.50;
  if (preco <= 35) return 5.00;
  if (preco <= 45) return 5.50;
  if (preco <= 55) return 6.00;
  if (preco <= 70) return 6.50;
  if (preco <= 90) return 7.00;
  if (preco <= 120) return 7.50;
  return 8.00;
}

export function calcularMargem(fob, landed, preco) {
  const lucro = preco - landed;
  return preco > 0 ? (lucro / preco) : 0;
}

export function calcularLandedCost(fob, modo = 'lcl', volume = 0.01) {
  // Taxas reais do Brasil
  const ii = 0.16;           // Imposto de Importação
  const ipi = 0.05;          // IPI
  const pisCofins = 0.1175;  // PIS + COFINS
  const icms = 0.18;         // ICMS SP
  const afrmm = 0.25;        // AFRMM (25% do frete)
  
  // Frete estimado
  let frete = 0;
  if (modo === 'aereo') frete = volume * 6 * 1000;
  else if (modo === 'fcl20') frete = 2200;
  else frete = volume * 180; // lcl
  
  // CIF
  const cif = fob + frete + (fob * 0.003); // 0.3% seguro
  
  // Impostos
  const iiValor = cif * ii;
  const ipiValor = (cif + iiValor) * ipi;
  const pisCofinsValor = cif * pisCofins;
  
  // ICMS por dentro (base de cálculo inclui todos os impostos)
  const baseIcms = (cif + iiValor + ipiValor + pisCofinsValor) / (1 - icms);
  const icmsValor = baseIcms * icms;
  
  // AFRMM
  const afrmmValor = frete * afrmm;
  
  // Total landed
  const landed = cif + iiValor + ipiValor + pisCofinsValor + icmsValor + afrmmValor;
  
  return {
    cif: cif.toFixed(2),
    ii: iiValor.toFixed(2),
    ipi: ipiValor.toFixed(2),
    pisCofins: pisCofinsValor.toFixed(2),
    icms: icmsValor.toFixed(2),
    afrmm: afrmmValor.toFixed(2),
    landed: landed.toFixed(2),
  };
}
