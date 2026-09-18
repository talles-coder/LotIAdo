import { StyleSheet } from 'react-native';

import { colors, radius } from './tokens';

/** Estilo de card reutilizado nas telas de domínio — ver `card-surface` em docs/design/lovable-mapeamento.md. */
export const shared = StyleSheet.create({
  cardSurface: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.xl,
    shadowColor: colors.earth,
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
});
