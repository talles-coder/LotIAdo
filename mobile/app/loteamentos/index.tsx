import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ChevronRight } from 'lucide-react-native';

import { listarLoteamentos, type Loteamento } from '../../src/api/loteamentos';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

export default function LoteamentosScreen() {
  const query = useQuery({ queryKey: ['loteamentos'], queryFn: listarLoteamentos });

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
      <FlatList
        data={query.data}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={query.isRefetching}
            onRefresh={() => query.refetch()}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
        ListEmptyComponent={<Text style={styles.empty}>Nenhum loteamento cadastrado ainda.</Text>}
        renderItem={({ item }: { item: Loteamento }) => (
          <Pressable
            style={({ pressed }) => [shared.cardSurface, styles.card, pressed && styles.cardPressed]}
            onPress={() => router.push(`/loteamentos/${item.id}`)}
          >
            <View style={styles.cardBody}>
              <Text style={styles.cardTitle}>{item.nome}</Text>
              {item.descricao ? <Text style={styles.cardSubtitle}>{item.descricao}</Text> : null}
            </View>
            <ChevronRight size={20} color={colors.mutedForeground} />
          </Pressable>
        )}
      />
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
  list: {
    padding: 16,
    paddingTop: 4,
    gap: 12,
  },
  card: {
    padding: 16,
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
