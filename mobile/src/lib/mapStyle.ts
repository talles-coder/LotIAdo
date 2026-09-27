import type { Map } from 'maplibre-gl';

export type CamadaMapaBase = 'ruas' | 'satelite';

/**
 * Basemap com duas camadas raster (ruas OSM + satélite Esri), sempre as duas presentes no style
 * e alternadas por visibilidade de layer (`alternarCamadaBase`) — nunca via `map.setStyle()`, que
 * derrubaria fontes/camadas adicionadas depois via imperativo (desenho do terra-draw, overlay de
 * planta calibrada em `PoligonoEditorMapa.web.tsx`).
 *
 * Continua sem conta/chave de API (decisão D10 em docs/03-decisoes-tecnicas.md): a Esri World
 * Imagery é um serviço público gratuito, mesmo padrão de uso do OSM.
 *
 * Sem type annotation de propósito: `maplibre-gl` (web) e `@maplibre/maplibre-react-native`
 * (nativo) declaram cada um seu próprio `StyleSpecification` — nominalmente incompatíveis (ex.
 * `center` como tupla vs. array) mesmo sendo o mesmo formato de JSON. Cada consumidor casta pro
 * tipo do seu próprio pacote (`as unknown as StyleSpecification`) na hora de usar.
 */
export const MAPA_ESTILO = {
  version: 8,
  sources: {
    ruas: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 19,
      attribution: '© OpenStreetMap contributors',
    },
    satelite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      // 18, não 19: em z19 a Esri devolve um tile placeholder ("Map data not yet available") pra
      // várias áreas fora de grandes centros urbanos (confirmado em Mogi Mirim/SP) — com
      // `maxzoom: 18` o MapLibre reusa (upscale) o tile de z18 real em vez de pedir o z19 vazio,
      // não importa o quanto o usuário dê zoom.
      maxzoom: 18,
      attribution: 'Esri, Maxar, Earthstar Geographics',
    },
  },
  layers: [
    { id: 'ruas', type: 'raster', source: 'ruas' },
    { id: 'satelite', type: 'raster', source: 'satelite', layout: { visibility: 'none' } },
  ],
};

/** Mostra só a camada base escolhida (a outra some) — as duas já existem no style desde o início. */
export function alternarCamadaBase(map: Map, camada: CamadaMapaBase): void {
  map.setLayoutProperty('ruas', 'visibility', camada === 'ruas' ? 'visible' : 'none');
  map.setLayoutProperty('satelite', 'visibility', camada === 'satelite' ? 'visible' : 'none');
}
