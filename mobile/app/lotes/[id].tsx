import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { obterLote } from '../../src/api/loteamentos';
import { formatArea, formatBRL } from '../../src/lib/format';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';
import { StatusBadge } from '../../src/components/StatusBadge';

export default function LoteDetalheScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const query = useQuery({ queryKey: ['lotes', id], queryFn: () => obterLote(id) });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {query.data?.identificacao ?? 'Lote'}
        </Text>
      </View>

      {query.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : query.isError || !query.data ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar o lote.</Text>
          <Button mode="outlined" onPress={() => query.refetch()} style={styles.retryButton}>
            Tentar novamente
          </Button>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.body}
          refreshControl={
            <RefreshControl
              refreshing={query.isRefetching}
              onRefresh={() => query.refetch()}
              colors={[colors.primary]}
              tintColor={colors.primary}
            />
          }
        >
          <View style={styles.titleRow}>
            <View>
              <Text style={styles.quadra}>{query.data.quadra ?? 'Sem quadra informada'}</Text>
              <Text style={styles.identificacao}>{query.data.identificacao}</Text>
            </View>
            <StatusBadge status={query.data.status} />
          </View>

          {query.data.preco ? (
            <View style={[shared.cardSurface, styles.priceCard]}>
              <Text style={styles.priceLabel}>Preço</Text>
              <Text style={styles.priceValue}>{formatBRL(query.data.preco)}</Text>
            </View>
          ) : null}

          <View style={styles.specsRow}>
            <View style={[shared.cardSurface, styles.specCard]}>
              <Text style={styles.specValue}>{formatArea(query.data.area_m2) ?? '—'}</Text>
              <Text style={styles.specLabel}>Área</Text>
            </View>
            <View style={[shared.cardSurface, styles.specCard]}>
              <Text style={styles.specValue}>{query.data.quadra ?? '—'}</Text>
              <Text style={styles.specLabel}>Quadra</Text>
            </View>
          </View>

          {query.data.caracteristicas && Object.keys(query.data.caracteristicas).length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Características</Text>
              <View style={styles.chips}>
                {Object.entries(query.data.caracteristicas).map(([key, value]) => (
                  <View key={key} style={styles.chip}>
                    <Text style={styles.chipText}>
                      {value === true ? key : `${key}: ${String(value)}`}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </ScrollView>
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
  body: {
    padding: 20,
    paddingTop: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  quadra: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  identificacao: {
    fontFamily: fonts.displayBold,
    fontSize: 26,
    color: colors.foreground,
  },
  priceCard: {
    marginTop: 16,
    padding: 16,
  },
  priceLabel: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  priceValue: {
    fontFamily: fonts.displayBold,
    fontSize: 26,
    color: colors.primary,
    marginTop: 2,
  },
  specsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  specCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
  },
  specValue: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
    color: colors.foreground,
  },
  specLabel: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
    marginTop: 2,
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  chip: {
    backgroundColor: colors.secondary,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.secondaryForeground,
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
