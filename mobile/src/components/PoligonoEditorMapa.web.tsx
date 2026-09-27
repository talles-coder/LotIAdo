import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Map, NavigationControl, type MapOptions } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { TerraDraw, TerraDrawPolygonMode, TerraDrawSelectMode, type GeoJSONStoreFeatures } from 'terra-draw';
import { TerraDrawMapLibreGLAdapter } from 'terra-draw-maplibre-gl-adapter';

import type { GeoJsonPolygon } from '../api/loteamentos';
import { alternarCamadaBase, MAPA_ESTILO, type CamadaMapaBase } from '../lib/mapStyle';
import { colors, fonts } from '../theme/tokens';
import type { PoligonoEditorMapaProps } from './PoligonoEditorMapa';

type StyleSpecification = NonNullable<MapOptions['style']>;

const CENTRO_PADRAO: [number, number] = [-47.9292, -15.7801]; // Brasília, só um fallback sem loteamento georreferenciado ainda.

function extrairPrimeiroPoligono(draw: TerraDraw): GeoJsonPolygon | null {
  const feature = draw
    .getSnapshot()
    .find((f: GeoJSONStoreFeatures) => f.geometry.type === 'Polygon');
  if (!feature) return null;
  return { type: 'Polygon', coordinates: feature.geometry.coordinates as number[][][] };
}

/**
 * Editor de polígono do backoffice web (FASE5-IMPL-03): desenha/revisa a geometria de um lote sobre
 * o mesmo mapa (maplibre-gl) usado em `LoteamentoMap.web.tsx`, usando `terra-draw` como camada de
 * desenho. Opcionalmente sobrepõe uma planta não georreferenciada já calibrada (`imagemOverlay`).
 */
export function PoligonoEditorMapa({
  poligonoInicial,
  centro,
  imagemOverlay,
  onGeometriaChange,
}: PoligonoEditorMapaProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const drawRef = useRef<TerraDraw | null>(null);
  const onChangeRef = useRef(onGeometriaChange);
  onChangeRef.current = onGeometriaChange;
  const [camadaBase, setCamadaBase] = useState<CamadaMapaBase>('ruas');

  useEffect(() => {
    if (!containerRef.current) return;

    const centroInicial =
      centro ?? (poligonoInicial ? (poligonoInicial.coordinates[0][0] as [number, number]) : CENTRO_PADRAO);

    const map = new Map({
      container: containerRef.current,
      style: MAPA_ESTILO as unknown as StyleSpecification,
      center: centroInicial,
      zoom: poligonoInicial || imagemOverlay ? 18 : 15,
    });
    mapRef.current = map;
    map.addControl(new NavigationControl(), 'top-right');

    const draw = new TerraDraw({
      adapter: new TerraDrawMapLibreGLAdapter({ map }),
      modes: [
        new TerraDrawPolygonMode(),
        new TerraDrawSelectMode({
          flags: {
            polygon: {
              feature: {
                draggable: true,
                coordinates: { draggable: true, deletable: true, midpoints: true },
              },
            },
          },
        }),
      ],
    });
    drawRef.current = draw;

    map.on('load', () => {
      if (imagemOverlay) {
        map.addSource('planta-calibrada', {
          type: 'image',
          url: imagemOverlay.url,
          coordinates: imagemOverlay.cantos,
        });
        map.addLayer({ id: 'planta-calibrada', type: 'raster', source: 'planta-calibrada', paint: { 'raster-opacity': 0.75 } });
      }

      draw.start();
      if (poligonoInicial) {
        try {
          const id = draw.getFeatureId();
          draw.addFeatures([
            { id, type: 'Feature', properties: { mode: 'polygon' }, geometry: poligonoInicial },
          ]);
          draw.setMode('select');
          draw.selectFeature(id);
        } catch {
          draw.setMode('polygon');
        }
      } else {
        draw.setMode('polygon');
      }
      onChangeRef.current(extrairPrimeiroPoligono(draw));
    });

    draw.on('finish', () => onChangeRef.current(extrairPrimeiroPoligono(draw)));
    draw.on('change', () => onChangeRef.current(extrairPrimeiroPoligono(draw)));

    return () => {
      draw.stop();
      map.remove();
      mapRef.current = null;
      drawRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    backgroundColor: colors.background,
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
