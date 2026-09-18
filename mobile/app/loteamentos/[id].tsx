import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, ChevronRight } from 'lucide-react-native';

import { listarLotes, obterLoteamento, type Lote } from '../../src/api/loteamentos';
import { formatArea } from '../../src/lib/format';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';
import { StatusBadge } from '../../src/components/StatusBadge';

export default function LotesDoLoteamentoScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const loteamentoQuery = useQuery({
    queryKey: ['loteamentos', id],
    queryFn: () => obterLoteamento(id),
  });
  const lotesQuery = useQuery({
    queryKey: ['loteamentos', id, 'lotes'],
    queryFn: () => listarLotes(id),
  });

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
          <Text style={styles.headerSubtitle}>
            {lotesQuery.data ? `${lotesQuery.data.length} lotes` : ' '}
          </Text>
        </View>
      </View>

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
          data={lotesQuery.data}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={lotesQuery.isRefetching || loteamentoQuery.isRefetching}
              onRefresh={handleRefresh}
              colors={[colors.primary]}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={<Text style={styles.empty}>Nenhum lote cadastrado neste loteamento.</Text>}
          renderItem={({ item }: { item: Lote }) => (
            <Pressable
              style={({ pressed }) => [shared.cardSurface, styles.card, pressed && styles.cardPressed]}
              onPress={() => router.push(`/lotes/${item.id}`)}
            >
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{item.identificacao}</Text>
                <Text style={styles.cardSubtitle}>
                  {[item.quadra, formatArea(item.area_m2)].filter(Boolean).join(' · ') || '—'}
                </Text>
              </View>
              <StatusBadge status={item.status} />
            </Pressable>
          )}
        />
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
  headerText: {
    flex: 1,
  },
  headerTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  headerSubtitle: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  list: {
    padding: 16,
    paddingTop: 4,
    gap: 10,
  },
  card: {
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardPressed: {
    backgroundColor: colors.muted,
  },
  cardBody: {
    flex: 1,
  },
  cardTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  cardSubtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    marginTop: 2,
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
