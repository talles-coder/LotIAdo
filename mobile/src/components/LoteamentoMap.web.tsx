import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

import type { GeoJsonPolygon, LoteStatus } from '../api/loteamentos';
import { colors } from '../theme/tokens';

export interface PoligonoMapa {
  id: string;
  status: LoteStatus;
  geometria: GeoJsonPolygon;
}

interface LoteamentoMapProps {
  poligonos: PoligonoMapa[];
  onSelect: (id: string) => void;
}

/** Stand-in até FASE5-IMPL-03 (maplibre-gl); evita carregar o módulo nativo do MapLibre no bundle web. */
export function LoteamentoMap(_props: LoteamentoMapProps) {
  return (
    <View style={styles.container}>
      <Text>Mapa disponível em breve na versão web.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
});
