import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button } from 'react-native-paper';
import { Text } from 'react-native-paper';
import { Sparkles } from 'lucide-react-native';

import { colors, fonts } from '../theme/tokens';
import type { CalibragemImagemProps } from './CalibragemImagem.types';

/**
 * Marcação de pontos de referência sobre a imagem da planta (FASE5-IMPL-03): o usuário clica na
 * imagem para marcar um ponto e informa a coordenada real correspondente (endereço/GPS já resolvido).
 *
 * Opcionalmente sobrepõe a "camada de sugestão da IA" (FASE8-IMPL-02/SCRUM-100): contornos e
 * identificações candidatas, vindos do OCR/detecção de contornos rodados no backend — sempre em
 * pixel da imagem original, nunca aplicados sem o usuário escolher um contorno e confirmar a
 * calibragem (nenhuma geometria é persistida a partir daqui).
 */
export function CalibragemImagem({
  imagemUri,
  tamanhoImagem,
  onMedirImagem,
  pontos,
  pontoPendente,
  onMarcarPonto,
  onConfirmarPonto,
  sugestao,
  sugestaoCarregando,
  contornoSelecionado,
  onSelecionarContorno,
}: CalibragemImagemProps) {
  const [lng, setLng] = useState('');
  const [lat, setLat] = useState('');
  const [tamanhoNatural, setTamanhoNatural] = useState<{ width: number; height: number } | null>(null);

  // Contornos/bboxes chegam nas dimensões reais do arquivo enviado; a imagem exibida costuma vir
  // escalada (`maxWidth: 100%`) — sem esse fator, a camada de sugestão desalinharia da planta.
  const escala = tamanhoImagem && tamanhoNatural ? tamanhoImagem.width / tamanhoNatural.width : null;

  return (
    <View style={styles.wrap}>
      {sugestao ? (
        <View style={styles.sugestaoBanner}>
          <Sparkles size={14} color={colors.primary} />
          <Text style={styles.sugestaoBannerTexto}>
            Sugestão da IA — toque num contorno para usar como ponto de partida do polígono
          </Text>
        </View>
      ) : sugestaoCarregando ? (
        <View style={styles.sugestaoBanner}>
          <Text style={styles.sugestaoBannerTexto}>Analisando a planta (OCR + contornos)…</Text>
        </View>
      ) : null}
      <View style={styles.imagemWrap}>
        {/* eslint-disable-next-line jsx-a11y/alt-text */}
        <img
          src={imagemUri}
          onLoad={(e) => {
            const img = e.currentTarget;
            setTamanhoNatural({ width: img.naturalWidth, height: img.naturalHeight });
            if (!tamanhoImagem) onMedirImagem({ width: img.clientWidth, height: img.clientHeight });
          }}
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            onMarcarPonto([e.clientX - rect.left, e.clientY - rect.top]);
          }}
          style={{ maxWidth: '100%', display: 'block', cursor: 'crosshair' }}
        />
        {sugestao && tamanhoImagem && escala ? (
          <svg
            width={tamanhoImagem.width}
            height={tamanhoImagem.height}
            // `pointerEvents: 'none'` no <svg> raiz: sem isso, ele absorve cliques na área
            // inteira (mesmo fora dos polígonos pintados), o que travaria a marcação de pontos
            // de calibração em qualquer lugar da imagem assim que a sugestão carrega.
            style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
          >
            {sugestao.contornos.map((contorno, i) => (
              <polygon
                key={i}
                points={contorno.pontos.map(([x, y]) => `${x * escala},${y * escala}`).join(' ')}
                fill={i === contornoSelecionado ? 'rgba(37, 99, 235, 0.35)' : 'rgba(37, 99, 235, 0.12)'}
                stroke={colors.primary}
                strokeWidth={i === contornoSelecionado ? 3 : 1.5}
                style={{ cursor: 'pointer', pointerEvents: 'auto' }}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelecionarContorno?.(i === contornoSelecionado ? null : i);
                }}
              />
            ))}
            {sugestao.identificacoes.map((identificacao, i) => (
              <text
                key={i}
                x={identificacao.bbox[0] * escala}
                y={Math.max(0, identificacao.bbox[1] * escala - 4)}
                fill={colors.primary}
                fontSize={11}
                style={{ pointerEvents: 'none' }}
              >
                {identificacao.texto}
              </text>
            ))}
          </svg>
        ) : null}
        {pontos.map((ponto, i) => (
          <View key={i} style={[styles.marcador, { left: ponto.pixel[0] - 8, top: ponto.pixel[1] - 8 }]}>
            <Text style={styles.marcadorTexto}>{i + 1}</Text>
          </View>
        ))}
      </View>
      {pontoPendente && (
        <View style={styles.formPonto}>
          <Text style={styles.formPontoLabel}>Ponto {pontos.length + 1}: informe a coordenada real</Text>
          <View style={styles.formPontoRow}>
            <input placeholder="Longitude" value={lng} onChange={(e) => setLng(e.target.value)} style={inputStyle} />
            <input placeholder="Latitude" value={lat} onChange={(e) => setLat(e.target.value)} style={inputStyle} />
            <Button
              mode="contained"
              onPress={() => {
                onConfirmarPonto(lng, lat);
                setLng('');
                setLat('');
              }}
            >
              Adicionar
            </Button>
          </View>
        </View>
      )}
    </View>
  );
}

const inputStyle = {
  padding: 10,
  borderRadius: 8,
  border: `1px solid ${colors.border}`,
  fontFamily: fonts.body,
  minWidth: 120,
};

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    padding: 16,
  },
  imagemWrap: {
    alignSelf: 'flex-start',
  },
  sugestaoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  sugestaoBannerTexto: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.primary,
  },
  marcador: {
    position: 'absolute',
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  marcadorTexto: {
    color: colors.primaryForeground,
    fontSize: 10,
    fontFamily: fonts.bodySemiBold,
  },
  formPonto: {
    marginTop: 16,
    padding: 12,
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  formPontoLabel: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
  formPontoRow: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
});
