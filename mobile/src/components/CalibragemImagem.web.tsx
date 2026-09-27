import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button } from 'react-native-paper';
import { Text } from 'react-native-paper';

import { colors, fonts } from '../theme/tokens';
import type { CalibragemImagemProps } from './CalibragemImagem.types';

/**
 * Marcação de pontos de referência sobre a imagem da planta (FASE5-IMPL-03): o usuário clica na
 * imagem para marcar um ponto e informa a coordenada real correspondente (endereço/GPS já resolvido).
 */
export function CalibragemImagem({
  imagemUri,
  tamanhoImagem,
  onMedirImagem,
  pontos,
  pontoPendente,
  onMarcarPonto,
  onConfirmarPonto,
}: CalibragemImagemProps) {
  const [lng, setLng] = useState('');
  const [lat, setLat] = useState('');

  return (
    <View style={styles.wrap}>
      {/* eslint-disable-next-line jsx-a11y/alt-text */}
      <img
        src={imagemUri}
        onLoad={(e) => {
          const img = e.currentTarget;
          if (!tamanhoImagem) onMedirImagem({ width: img.clientWidth, height: img.clientHeight });
        }}
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          onMarcarPonto([e.clientX - rect.left, e.clientY - rect.top]);
        }}
        style={{ maxWidth: '100%', display: 'block', cursor: 'crosshair' }}
      />
      {pontos.map((ponto, i) => (
        <View key={i} style={[styles.marcador, { left: ponto.pixel[0] - 8, top: ponto.pixel[1] - 8 }]}>
          <Text style={styles.marcadorTexto}>{i + 1}</Text>
        </View>
      ))}
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
