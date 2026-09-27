import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

import type { GeoJsonPolygon } from '../api/loteamentos';
import { colors } from '../theme/tokens';

export type Canto = [number, number];

export interface ImagemOverlay {
  url: string;
  /** 4 cantos [lng, lat], em ordem: superior-esquerdo, superior-direito, inferior-direito, inferior-esquerdo. */
  cantos: [Canto, Canto, Canto, Canto];
}

export interface PoligonoEditorMapaProps {
  poligonoInicial: GeoJsonPolygon | null;
  centro?: [number, number];
  imagemOverlay?: ImagemOverlay | null;
  onGeometriaChange: (geometria: GeoJsonPolygon | null) => void;
}

/** Editor de polígono é uma ferramenta de backoffice web (FASE5-IMPL-03) — sem versão nativa por escopo. */
export function PoligonoEditorMapa(_props: PoligonoEditorMapaProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Edição de geometria disponível apenas no backoffice web.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background, padding: 24 },
  text: { textAlign: 'center', color: colors.mutedForeground },
});
