/**
 * Calibração/georreferenciamento manual de plantas não georreferenciadas (FASE5-IMPL-03,
 * docs/01-analise-requisitos.md seção 8): a partir de 2–3 pontos de referência conhecidos
 * (pixel na imagem <-> coordenada real), resolve a transformação que converte qualquer ponto
 * da imagem para lng/lat (SRID 4326).
 */
export interface PontoReferencia {
  /** Posição do ponto marcado na imagem (pixels, origem no canto superior-esquerdo). */
  pixel: [number, number];
  /** Coordenada real conhecida daquele ponto (endereço/GPS já resolvido para lng/lat). */
  lngLat: [number, number];
}

export interface TransformacaoAfim {
  aplicar: (pixel: [number, number]) => [number, number];
}

export function calibrarTransformacao(pontos: PontoReferencia[]): TransformacaoAfim {
  if (pontos.length < 2) {
    throw new Error('São necessários pelo menos 2 pontos de referência para calibrar a planta');
  }
  return pontos.length === 2 ? calibrarSimilaridade(pontos[0], pontos[1]) : calibrarAfimMinimosQuadrados(pontos);
}

/** Com exatamente 2 pontos: rotação + escala uniforme + translação (sem cisalhamento), via aritmética complexa. */
function calibrarSimilaridade(p1: PontoReferencia, p2: PontoReferencia): TransformacaoAfim {
  const dPixelX = p2.pixel[0] - p1.pixel[0];
  const dPixelY = p2.pixel[1] - p1.pixel[1];
  const dAlvoLng = p2.lngLat[0] - p1.lngLat[0];
  const dAlvoLat = p2.lngLat[1] - p1.lngLat[1];
  const denom = dPixelX * dPixelX + dPixelY * dPixelY;
  if (denom < 1e-12) {
    throw new Error('Os dois pontos de referência não podem coincidir na imagem');
  }
  // k = dAlvo / dPixel (divisão de números complexos: dPixel = x + iy, dAlvo = lng + i*lat).
  const kReal = (dAlvoLng * dPixelX + dAlvoLat * dPixelY) / denom;
  const kImag = (dAlvoLat * dPixelX - dAlvoLng * dPixelY) / denom;
  return {
    aplicar: ([x, y]) => {
      const dx = x - p1.pixel[0];
      const dy = y - p1.pixel[1];
      return [p1.lngLat[0] + (kReal * dx - kImag * dy), p1.lngLat[1] + (kImag * dx + kReal * dy)];
    },
  };
}

/** Com 3+ pontos: afim geral (6 parâmetros) por mínimos quadrados (equações normais). */
function calibrarAfimMinimosQuadrados(pontos: PontoReferencia[]): TransformacaoAfim {
  const linhas = pontos.map((p) => [p.pixel[0], p.pixel[1], 1]);

  const AtA: number[][] = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
  ];
  const AtLng = [0, 0, 0];
  const AtLat = [0, 0, 0];
  linhas.forEach((linha, idx) => {
    const [lng, lat] = pontos[idx].lngLat;
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        AtA[i][j] += linha[i] * linha[j];
      }
      AtLng[i] += linha[i] * lng;
      AtLat[i] += linha[i] * lat;
    }
  });

  const [a, b, e] = resolverSistema3x3(AtA.map((linha) => [...linha]), AtLng);
  const [c, d, f] = resolverSistema3x3(AtA.map((linha) => [...linha]), AtLat);

  return {
    aplicar: ([x, y]) => [a * x + b * y + e, c * x + d * y + f],
  };
}

/** Eliminação de Gauss com pivô parcial para um sistema 3x3 (`A * resultado = b`). */
function resolverSistema3x3(A: number[][], b: number[]): number[] {
  const m = A.map((linha, i) => [...linha, b[i]]);
  for (let col = 0; col < 3; col++) {
    let pivo = col;
    for (let linha = col + 1; linha < 3; linha++) {
      if (Math.abs(m[linha][col]) > Math.abs(m[pivo][col])) pivo = linha;
    }
    [m[col], m[pivo]] = [m[pivo], m[col]];
    if (Math.abs(m[col][col]) < 1e-9) {
      throw new Error('Pontos de referência insuficientes ou colineares para calibrar a planta');
    }
    for (let linha = 0; linha < 3; linha++) {
      if (linha === col) continue;
      const fator = m[linha][col] / m[col][col];
      for (let k = col; k < 4; k++) m[linha][k] -= fator * m[col][k];
    }
  }
  return [m[0][3] / m[0][0], m[1][3] / m[1][1], m[2][3] / m[2][2]];
}
