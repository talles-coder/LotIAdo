import { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useQueries, useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ChevronRight, MapPin, Search } from 'lucide-react-native';

import { listarLoteamentos, listarLotes, type Loteamento } from '../../src/api/loteamentos';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';
import { BottomNav } from '../../src/components/BottomNav';

export default function LoteamentosScreen() {
  const [search, setSearch] = useState('');
  const query = useQuery({ queryKey: ['loteamentos'], queryFn: listarLoteamentos });

  const loteamentos = query.data ?? [];
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return loteamentos;
    return loteamentos.filter(
      (l) => l.nome.toLowerCase().includes(term) || l.descricao?.toLowerCase().includes(term),
    );
  }, [loteamentos, search]);

  // Disponibilidade por loteamento (barra de progresso) reaproveita a mesma queryKey da tela de
  // lista de lotes — navegar pra dentro de um loteamento não refaz essa chamada.
  const lotesQueries = useQueries({
    queries: loteamentos.map((l) => ({
      queryKey: ['loteamentos', l.id, 'lotes'],
      queryFn: () => listarLotes(l.id),
    })),
  });
  const disponibilidadePorLoteamento = useMemo(() => {
    const map = new Map<string, { disponiveis: number; total: number }>();
    loteamentos.forEach((l, index) => {
      const lotes = lotesQueries[index]?.data;
      if (lotes) {
        map.set(l.id, { disponiveis: lotes.filter((lote) => lote.status === 'disponivel').length, total: lotes.length });
      }
    });
    return map;
  }, [loteamentos, lotesQueries]);

  if (query.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (query.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Não foi possível carregar os loteamentos.</Text>
        <Button mode="outlined" onPress={() => query.refetch()} style={styles.retryButton}>
          Tentar novamente
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Loteamentos</Text>

      <View style={styles.searchWrapper}>
        <Search size={18} color={colors.mutedForeground} style={styles.searchIcon} />
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Buscar por nome ou cidade"
          placeholderTextColor={colors.mutedForeground}
          style={styles.searchInput}
        />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        style={styles.listFlex}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={query.isRefetching}
            onRefresh={() => query.refetch()}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
        ListEmptyComponent={<Text style={styles.empty}>Nenhum loteamento encontrado.</Text>}
        renderItem={({ item }: { item: Loteamento }) => {
          const disponibilidade = disponibilidadePorLoteamento.get(item.id);
          const pct = disponibilidade && disponibilidade.total > 0
            ? Math.round((disponibilidade.disponiveis / disponibilidade.total) * 100)
            : null;

          return (
            <Pressable
              style={({ pressed }) => [shared.cardSurface, styles.card, pressed && styles.cardPressed]}
              onPress={() => router.push(`/loteamentos/${item.id}`)}
            >
              <View style={styles.cardHeader}>
                <View style={styles.cardHeaderText}>
                  <Text style={styles.cardTitle}>{item.nome}</Text>
                  {item.descricao ? (
                    <View style={styles.cardLocation}>
                      <MapPin size={13} color={colors.mutedForeground} />
                      <Text style={styles.cardSubtitle}>{item.descricao}</Text>
                    </View>
                  ) : null}
                </View>
                <ChevronRight size={20} color={colors.mutedForeground} />
              </View>

              {disponibilidade && pct !== null ? (
                <>
                  <View style={styles.availabilityRow}>
                    <Text style={styles.availabilityText}>
                      <Text style={styles.availabilityCount}>{disponibilidade.disponiveis}</Text> disponíveis de{' '}
                      {disponibilidade.total}
                    </Text>
                    <Text style={styles.availabilityPct}>{pct}%</Text>
                  </View>
                  <View style={styles.progressTrack}>
                    <View style={[styles.progressFill, { width: `${pct}%` }]} />
                  </View>
                </>
              ) : null}
            </Pressable>
          );
        }}
      />

      <BottomNav />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingTop: 20,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
    padding: 24,
    gap: 12,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.foreground,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  searchWrapper: {
    marginHorizontal: 16,
    marginBottom: 4,
    position: 'relative',
    justifyContent: 'center',
  },
  searchIcon: {
    position: 'absolute',
    left: 14,
    zIndex: 1,
  },
  searchInput: {
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    paddingLeft: 42,
    paddingRight: 14,
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.foreground,
  },
  listFlex: {
    flex: 1,
  },
  list: {
    padding: 16,
    paddingTop: 12,
    gap: 12,
  },
  card: {
    padding: 16,
  },
  cardPressed: {
    backgroundColor: colors.muted,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  cardHeaderText: {
    flex: 1,
  },
  cardTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  cardLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  cardSubtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  availabilityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginTop: 12,
  },
  availabilityText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
  },
  availabilityCount: {
    fontFamily: fonts.displayBold,
    fontSize: 18,
    color: colors.status.disponivel.text,
  },
  availabilityPct: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.muted,
    marginTop: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 999,
    backgroundColor: colors.status.disponivel.text,
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
