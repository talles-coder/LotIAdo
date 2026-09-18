/**
 * Tokens da identidade visual do LotIAdo, mapeados a partir do repo gerado
 * no Lovable — ver docs/design/lovable-mapeamento.md (fonte de verdade).
 * `primary` é o único token pensado pra ser trocado por tenant no futuro.
 */
export const colors = {
  background: '#FDFAF4',
  foreground: '#271D17',
  card: '#FFFFFF',

  primary: '#DB551D',
  primaryForeground: '#FEFBF8',
  primarySoft: '#FFE8DC',

  secondary: '#F5EDE4',
  secondaryForeground: '#3A2A20',

  muted: '#F5EFE7',
  mutedForeground: '#6F6056',

  accent: '#25984D',
  accentForeground: '#FEFBF8',
  accentSoft: '#DAF8DF',

  earth: '#442C22',
  earthForeground: '#F9F4EE',

  destructive: '#D73337',
  destructiveForeground: '#FEFBF8',

  border: '#E4DDD3',
  input: '#DDD6CD',

  /**
   * O enum real do backend (`LoteStatus`, backend/app/loteamentos_lotes/domain/state_machine.py)
   * tem 4 estados, não os 5 do repo de referência do Lovable — `indisponivel` cobre o que lá
   * era `bloqueado` (estado administrativo que bloqueia ação, só retorna a `disponivel`).
   */
  status: {
    disponivel: { text: '#007F35', soft: '#D8F9DD' },
    reservado: { text: '#B76C00', soft: '#FFF0C5' },
    vendido: { text: '#2A669F', soft: '#DDEDFF' },
    indisponivel: { text: '#C92F33', soft: '#FFE6E3' },
  },
} as const;

export const radius = {
  sm: 8,
  md: 10,
  lg: 12,
  xl: 16,
  full: 999,
} as const;

export const fonts = {
  display: 'Outfit_600SemiBold',
  displayBold: 'Outfit_700Bold',
  body: 'Figtree_400Regular',
  bodyMedium: 'Figtree_500Medium',
  bodySemiBold: 'Figtree_600SemiBold',
} as const;
