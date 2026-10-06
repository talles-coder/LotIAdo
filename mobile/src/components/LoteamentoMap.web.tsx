import { useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import {
  Map,
  NavigationControl,
  type GeoJSONSource,
  type LngLatBoundsLike,
  type MapLayerMouseEvent,
  type MapOptions,
} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

import type { GeoJsonPolygon, LoteStatus } from '../api/loteamentos';
import { colors } from '../theme/tokens';

type StyleSpecification = NonNullable<MapOptions['style']>;

export interface PoligonoMapa {
  id: string;
  status: LoteStatus;
  geometria: GeoJsonPolygon;
}

interface LoteamentoMapProps {
  poligonos: PoligonoMapa[];
  onSelect: (id: string) => void;
}

/** Mesmos tiles públicos do OSM usados no nativo (decisão D10 em docs/03-decisoes-tecnicas.md). */
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

function toBounds(poligonos: PoligonoMapa[]): LngLatBoundsLike | undefined {
  const pontos = poligonos.flatMap((p) => p.geometria.coordinates[0]);
  if (pontos.length === 0) return undefined;
  const lngs = pontos.map(([lng]) => lng);
  const lats = pontos.map(([, lat]) => lat);
  return [
    [Math.min(...lngs), Math.min(...lats)],
    [Math.max(...lngs), Math.max(...lats)],
  ];
}

function toFeatureCollection(poligonos: PoligonoMapa[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: poligonos.map((p) => ({
      type: 'Feature',
      properties: { id: p.id, status: p.status },
      geometry: p.geometria,
    })),
  };
}

/**
 * Versão web de `LoteamentoMap` (decisões D8/D10): mesma interface de props do componente nativo,
 * usando `maplibre-gl` diretamente (mesmo motor e estilo de mapa do nativo, sem wrapper comunitário).
 */
export function LoteamentoMap({ poligonos, onSelect }: LoteamentoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new Map({
      container: containerRef.current,
      style: MAP_STYLE,
      bounds: toBounds(poligonos),
      fitBoundsOptions: { padding: 48 },
    });
    mapRef.current = map;
    map.addControl(new NavigationControl(), 'top-right');

    map.on('load', () => {
      map.addSource('lotes', { type: 'geojson', data: toFeatureCollection(poligonos) });
      map.addLayer({
        id: 'lotes-fill',
        type: 'fill',
        source: 'lotes',
        paint: { 'fill-color': STATUS_COLOR_EXPR as never, 'fill-opacity': 0.7 },
      });
      map.addLayer({
        id: 'lotes-line',
        type: 'line',
        source: 'lotes',
        paint: { 'line-color': STATUS_COLOR_EXPR as never, 'line-width': 2 },
      });

      map.on('click', 'lotes-fill', (e: MapLayerMouseEvent) => {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === 'string') onSelectRef.current(id);
      });
      map.on('mouseenter', 'lotes-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'lotes-fill', () => {
        map.getCanvas().style.cursor = '';
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const source = map.getSource('lotes') as GeoJSONSource | undefined;
    if (source) {
      source.setData(toFeatureCollection(poligonos));
    }
  }, [poligonos]);

  return (
    <View style={styles.map}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </View>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
});
