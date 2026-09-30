import { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { listarLotes, obterLoteamento, type LoteStatus } from '../../../src/api/loteamentos';
import { LoteamentoMap, type PoligonoMapa } from '../../../src/components/LoteamentoMap';
import { colors, fonts } from '../../../src/theme/tokens';

const LEGENDA: { status: LoteStatus; label: string }[] = [
  { status: 'disponivel', label: 'Disponível' },
  { status: 'reservado', label: 'Reservado' },
  { status: 'vendido', label: 'Vendido' },
  { status: 'indisponivel', label: 'Indisponível' },
];

export default function MapaDoLoteamentoScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const loteamentoQuery = useQuery({
    queryKey: ['loteamentos', id],
    queryFn: () => obterLoteamento(id),
  });
  const lotesQuery = useQuery({
    queryKey: ['loteamentos', id, 'lotes'],
    queryFn: () => listarLotes(id),
  });

  const poligonos = useMemo<PoligonoMapa[]>(
    () =>
      (lotesQuery.data ?? []).flatMap((lote) =>
        lote.geometria ? [{ id: lote.id, status: lote.status, geometria: lote.geometria }] : [],
      ),
    [lotesQuery.data],
  );

  const isLoading = loteamentoQuery.isLoading || lotesQuery.isLoading;
  const isError = loteamentoQuery.isError || lotesQuery.isError;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {loteamentoQuery.data?.nome ?? 'Mapa'}
        </Text>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.message}>Não foi possível carregar o mapa.</Text>
          <Button
            mode="outlined"
            onPress={() => {
              loteamentoQuery.refetch();
              lotesQuery.refetch();
            }}
          >
            Tentar novamente
          </Button>
        </View>
      ) : poligonos.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.message}>Este loteamento ainda não tem lotes desenhados no mapa.</Text>
        </View>
      ) : (
        <>
          <LoteamentoMap poligonos={poligonos} onSelect={(loteId) => router.push(`/lotes/${loteId}`)} />
          <View style={styles.legend}>
            {LEGENDA.map((item) => (
              <View key={item.status} style={styles.legendItem}>
                <View style={[styles.dot, { backgroundColor: colors.status[item.status].text }]} />
                <Text style={styles.legendText}>{item.label}</Text>
              </View>
            ))}
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 12,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    flex: 1,
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  message: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
    textAlign: 'center',
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
});
