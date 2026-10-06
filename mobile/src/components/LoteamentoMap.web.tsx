import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
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
import { alternarCamadaBase, MAPA_ESTILO, type CamadaMapaBase } from '../lib/mapStyle';
import { colors, fonts } from '../theme/tokens';

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
  const [camadaBase, setCamadaBase] = useState<CamadaMapaBase>('ruas');

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new Map({
      container: containerRef.current,
      style: MAPA_ESTILO as unknown as StyleSpecification,
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

  function alternar() {
    const proxima = camadaBase === 'ruas' ? 'satelite' : 'ruas';
    setCamadaBase(proxima);
    if (mapRef.current) alternarCamadaBase(mapRef.current, proxima);
  }

  return (
    <View style={styles.map}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <Pressable style={styles.camadaBotao} onPress={alternar}>
        <Text style={styles.camadaBotaoTexto}>{camadaBase === 'ruas' ? 'Satélite' : 'Ruas'}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
  camadaBotao: {
    position: 'absolute',
    top: 12,
    left: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
  },
  camadaBotaoTexto: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
});
