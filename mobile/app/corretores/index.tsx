import { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, ChevronRight, Plus, Search } from 'lucide-react-native';

import { listarCorretores, type Corretor } from '../../src/api/corretores';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

export default function CorretoresScreen() {
  const [search, setSearch] = useState('');
  const query = useQuery({ queryKey: ['corretores'], queryFn: listarCorretores });

  const corretores = query.data ?? [];
  const filtrados = useMemo(() => {
    const termo = search.trim().toLowerCase();
    if (!termo) return corretores;
    return corretores.filter((c) => c.nome.toLowerCase().includes(termo));
  }, [corretores, search]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Corretores</Text>
        <Pressable onPress={() => router.push('/corretores/novo')} style={styles.backButton} hitSlop={8}>
          <Plus size={20} color={colors.foreground} />
        </Pressable>
      </View>

      <View style={styles.searchWrapper}>
        <Search size={18} color={colors.mutedForeground} style={styles.searchIcon} />
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Buscar por nome"
          placeholderTextColor={colors.mutedForeground}
          style={styles.searchInput}
        />
      </View>

      {query.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : query.isError ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar os corretores.</Text>
          <Button mode="outlined" onPress={() => query.refetch()}>
            Tentar novamente
          </Button>
        </View>
      ) : (
        <FlatList
          data={filtrados}
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
          ListEmptyComponent={<Text style={styles.empty}>Nenhum corretor cadastrado.</Text>}
          renderItem={({ item }: { item: Corretor }) => (
            <Pressable
              style={({ pressed }) => [shared.cardSurface, styles.card, pressed && styles.cardPressed]}
              onPress={() => router.push(`/corretores/${item.id}`)}
            >
              <View style={styles.cardText}>
                <Text style={styles.cardTitle}>{item.nome}</Text>
                <Text style={styles.cardSubtitle}>{item.contato}</Text>
              </View>
              <ChevronRight size={20} color={colors.mutedForeground} />
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
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
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
  searchWrapper: {
    marginHorizontal: 16,
    marginTop: 12,
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
  list: {
    padding: 16,
    paddingTop: 12,
    gap: 12,
  },
  card: {
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  cardPressed: {
    backgroundColor: colors.muted,
  },
  cardText: {
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
});
