import { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, ChevronRight, Map as MapIcon } from 'lucide-react-native';

import { listarLotes, obterLoteamento, type Lote, type LoteStatus } from '../../src/api/loteamentos';
import { formatArea, formatBRL } from '../../src/lib/format';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';
import { StatusBadge } from '../../src/components/StatusBadge';
import { BottomNav } from '../../src/components/BottomNav';

const FILTROS: { key: LoteStatus | 'todos'; label: string }[] = [
  { key: 'todos', label: 'Todos' },
  { key: 'disponivel', label: 'Disponíveis' },
  { key: 'reservado', label: 'Reservados' },
  { key: 'vendido', label: 'Vendidos' },
  { key: 'indisponivel', label: 'Indisponíveis' },
];

export default function LotesDoLoteamentoScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [filtro, setFiltro] = useState<LoteStatus | 'todos'>('todos');

  const loteamentoQuery = useQuery({
    queryKey: ['loteamentos', id],
    queryFn: () => obterLoteamento(id),
  });
  const lotesQuery = useQuery({
    queryKey: ['loteamentos', id, 'lotes'],
    queryFn: () => listarLotes(id),
  });

  const lotesFiltrados = useMemo(() => {
    if (!lotesQuery.data) return [];
    if (filtro === 'todos') return lotesQuery.data;
    return lotesQuery.data.filter((lote) => lote.status === filtro);
  }, [lotesQuery.data, filtro]);

  const isLoading = loteamentoQuery.isLoading || lotesQuery.isLoading;
  const isError = loteamentoQuery.isError || lotesQuery.isError;

  function handleRefresh() {
    loteamentoQuery.refetch();
    lotesQuery.refetch();
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <View style={styles.headerText}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {loteamentoQuery.data?.nome ?? 'Loteamento'}
          </Text>
        </View>
        <Pressable onPress={() => router.push(`/loteamentos/${id}/mapa`)} style={styles.backButton} hitSlop={8}>
          <MapIcon size={20} color={colors.foreground} />
        </Pressable>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filters} contentContainerStyle={styles.filtersContent}>
        {FILTROS.map((f) => {
          const active = filtro === f.key;
          return (
            <Pressable
              key={f.key}
              onPress={() => setFiltro(f.key)}
              style={[styles.filterChip, active && styles.filterChipActive]}
            >
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{f.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      {!isLoading && !isError && (
        <Text style={styles.count}>{lotesFiltrados.length} lotes</Text>
      )}

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar os lotes.</Text>
          <Button mode="outlined" onPress={handleRefresh} style={styles.retryButton}>
            Tentar novamente
          </Button>
        </View>
      ) : (
        <FlatList
          data={lotesFiltrados}
          keyExtractor={(item) => item.id}
          style={styles.listFlex}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={lotesQuery.isRefetching || loteamentoQuery.isRefetching}
              onRefresh={handleRefresh}
              colors={[colors.primary]}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={<Text style={styles.empty}>Nenhum lote encontrado.</Text>}
          renderItem={({ item }: { item: Lote }) => (
            <Pressable
              style={({ pressed }) => [
                shared.cardSurface,
                styles.card,
                { borderLeftColor: colors.status[item.status].text },
                pressed && styles.cardPressed,
              ]}
              onPress={() => router.push(`/lotes/${item.id}`)}
            >
              <View style={styles.cardBody}>
                <View style={styles.cardTitleRow}>
                  <Text style={styles.cardTitle}>{item.identificacao}</Text>
                  {item.quadra ? <Text style={styles.cardQuadra}>{item.quadra}</Text> : null}
                </View>
                <Text style={styles.cardSubtitle}>
                  {formatArea(item.area_m2) ?? '—'}
                  {item.preco ? (
                    <>
                      {' · '}
                      <Text style={styles.cardPrice}>{formatBRL(item.preco)}</Text>
                    </>
                  ) : null}
                </Text>
              </View>
              <StatusBadge status={item.status} />
            </Pressable>
          )}
        />
      )}

      <BottomNav />
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
  headerText: {
    flex: 1,
  },
  headerTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  filters: {
    flexGrow: 0,
  },
  filtersContent: {
    paddingHorizontal: 16,
    gap: 8,
    paddingBottom: 4,
  },
  filterChip: {
    height: 36,
    paddingHorizontal: 16,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
  filterChipTextActive: {
    color: colors.primaryForeground,
  },
  count: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  listFlex: {
    flex: 1,
  },
  list: {
    padding: 16,
    paddingTop: 8,
    gap: 10,
  },
  card: {
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderLeftWidth: 6,
    overflow: 'hidden',
  },
  cardPressed: {
    backgroundColor: colors.muted,
  },
  cardBody: {
    flex: 1,
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  cardTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  cardQuadra: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  cardSubtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    marginTop: 2,
  },
  cardPrice: {
    fontFamily: fonts.bodySemiBold,
    color: colors.foreground,
  },
  empty: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
    textAlign: 'center',
    marginTop: 32,
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 4,
  },
});
