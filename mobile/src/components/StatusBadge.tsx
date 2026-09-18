import { StyleSheet, Text, View } from 'react-native';

import type { LoteStatus } from '../api/loteamentos';
import { colors, fonts } from '../theme/tokens';

const LABELS: Record<LoteStatus, string> = {
  disponivel: 'Disponível',
  reservado: 'Reservado',
  vendido: 'Vendido',
  indisponivel: 'Indisponível',
};

/** Cor + texto + indicador (nunca só cor) — ver docs/design/lovable-mapeamento.md. */
export function StatusBadge({ status }: { status: LoteStatus }) {
  const tone = colors.status[status];
  return (
    <View style={[styles.badge, { backgroundColor: tone.soft }]}>
      <View style={[styles.dot, { backgroundColor: tone.text }]} />
      <Text style={[styles.label, { color: tone.text }]}>{LABELS[status]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  label: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
  },
});
