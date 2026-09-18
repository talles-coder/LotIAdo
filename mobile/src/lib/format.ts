export function formatBRL(value: string | null): string | null {
  if (value === null) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

export function formatArea(value: string | null): string | null {
  if (value === null) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return `${n.toLocaleString('pt-BR', { maximumFractionDigits: 0 })} m²`;
}
