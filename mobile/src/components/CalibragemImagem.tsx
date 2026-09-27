import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

import { colors } from '../theme/tokens';
import type { CalibragemImagemProps } from './CalibragemImagem.types';

/** Marcação de pontos de referência sobre a imagem é uma ferramenta de backoffice web. */
export function CalibragemImagem(_props: CalibragemImagemProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Calibração de planta disponível apenas no backoffice web.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  text: { textAlign: 'center', color: colors.mutedForeground },
});
