import { useMemo } from 'react';
import { StyleSheet } from 'react-native';
import {
  Camera,
  GeoJSONSource,
  Layer,
  Map,
  type LngLatBounds,
  type StyleSpecification,
} from '@maplibre/maplibre-react-native';

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

/** Tiles públicos do OSM: só para dev/demo (política de uso justo). Decisão D10 em docs/03-decisoes-tecnicas.md. */
const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 19,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

const STATUS_COLOR_EXPR = [
  'match',
  ['get', 'status'],
  ...(Object.keys(colors.status) as LoteStatus[]).flatMap((s) => [s, colors.status[s].text]),
  '#888888',
] as const;

function toBounds(poligonos: PoligonoMapa[]): LngLatBounds | undefined {
  const pontos = poligonos.flatMap((p) => p.geometria.coordinates[0]);
  if (pontos.length === 0) return undefined;
  const lngs = pontos.map(([lng]) => lng);
  const lats = pontos.map(([, lat]) => lat);
  return [Math.min(...lngs), Math.min(...lats), Math.max(...lngs), Math.max(...lats)];
}

/**
 * Mapa de lotes coloridos por status. Toda a lógica de mapa fica aqui: na Fase 5 este componente
 * ganha uma versão `.web.tsx` com a mesma interface de props (decisões D8/D10 em docs/03-decisoes-tecnicas.md).
 */
export function LoteamentoMap({ poligonos, onSelect }: LoteamentoMapProps) {
  const data = useMemo<GeoJSON.FeatureCollection>(
    () => ({
      type: 'FeatureCollection',
      features: poligonos.map((p) => ({
        type: 'Feature',
        properties: { id: p.id, status: p.status },
        geometry: p.geometria,
      })),
    }),
    [poligonos],
  );
  const bounds = useMemo(() => toBounds(poligonos), [poligonos]);

  return (
    <Map style={styles.map} mapStyle={MAP_STYLE}>
      {bounds && (
        <Camera initialViewState={{ bounds, padding: { top: 48, right: 48, bottom: 48, left: 48 } }} />
      )}
      <GeoJSONSource
        id="lotes"
        data={data}
        onPress={(e) => {
          const id = e.nativeEvent.features[0]?.properties?.id;
          if (typeof id === 'string') onSelect(id);
        }}
      >
        <Layer
          id="lotes-fill"
          type="fill"
          paint={{ 'fill-color': STATUS_COLOR_EXPR as never, 'fill-opacity': 0.7 }}
        />
        <Layer
          id="lotes-line"
          type="line"
          paint={{ 'line-color': STATUS_COLOR_EXPR as never, 'line-width': 2 }}
        />
      </GeoJSONSource>
    </Map>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
});
