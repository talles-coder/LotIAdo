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
  /** Grade de 2 colunas no navegador em tela larga (ver WebShell): View simples com `grid`/`gridItem`. */
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  gridItem: {
    width: '49%',
  },
  /** Mesma grade em FlatList (`numColumns` + `columnWrapperStyle`); a célula é a linha, então o item usa flex. */
  flatGridRow: {
    gap: 12,
  },
  flatGridItem: {
    flex: 1,
    maxWidth: '49.5%',
  },
  /**
   * Barra de ação fixa no rodapé (`footer` do `MobileShell` no repo de referência do
   * Lovable) — substitui o `BottomNav` sempre que a tela ganha uma ação principal.
   */
  stickyFooter: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 16,
    shadowColor: colors.earth,
    shadowOpacity: 0.1,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: -2 },
    elevation: 4,
  },
});
