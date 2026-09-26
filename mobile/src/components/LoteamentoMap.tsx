import { useCallback, useRef } from 'react';
import { StyleSheet } from 'react-native';
import MapView, { Polygon, PROVIDER_GOOGLE, type LatLng } from 'react-native-maps';

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

/** GeoJSON usa [lng, lat]; o react-native-maps espera { latitude, longitude }. */
function toLatLng(geometria: GeoJsonPolygon): LatLng[] {
  return geometria.coordinates[0].map(([longitude, latitude]) => ({ latitude, longitude }));
}

/**
 * Mapa de lotes coloridos por status. Toda a lógica de mapa fica aqui: na Fase 5 este componente
 * ganha uma versão `.web.tsx` com a mesma interface de props (decisão D8 em docs/03-decisoes-tecnicas.md).
 */
export function LoteamentoMap({ poligonos, onSelect }: LoteamentoMapProps) {
  const mapRef = useRef<MapView>(null);

  const ajustarAoLoteamento = useCallback(() => {
    const coordenadas = poligonos.flatMap((p) => toLatLng(p.geometria));
    if (coordenadas.length === 0) return;
    mapRef.current?.fitToCoordinates(coordenadas, {
      edgePadding: { top: 48, right: 48, bottom: 48, left: 48 },
      animated: false,
    });
  }, [poligonos]);

  return (
    <MapView
      ref={mapRef}
      style={styles.map}
      provider={PROVIDER_GOOGLE}
      mapType="satellite"
      onMapReady={ajustarAoLoteamento}
      onLayout={ajustarAoLoteamento}
    >
      {poligonos.map((p) => {
        const tone = colors.status[p.status];
        return (
          <Polygon
            key={`${p.id}-${p.status}`}
            coordinates={toLatLng(p.geometria)}
            fillColor={`${tone.text}B3`}
            strokeColor={tone.text}
            strokeWidth={2}
            tappable
            onPress={() => onSelect(p.id)}
          />
        );
      })}
    </MapView>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
});
