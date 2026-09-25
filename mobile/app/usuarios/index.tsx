import { Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, Plus } from 'lucide-react-native';

import { desativarMembership, listarMemberships, type Membership } from '../../src/api/usuarios';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

const PAPEL_LABEL: Record<string, string> = {
  admin: 'Admin',
  gestor: 'Gestor',
  corretor: 'Corretor',
};

export default function UsuariosScreen() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['usuarios', 'memberships'], queryFn: listarMemberships });

  const desativarMutation = useMutation({
    mutationFn: (membershipId: string) => desativarMembership(membershipId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios', 'memberships'] }),
    onError: (err) => Alert.alert('Não foi possível desativar', getErrorMessage(err, 'Tente novamente.')),
  });

  function confirmarDesativacao(membership: Membership) {
    Alert.alert(
      'Desativar acesso',
      `Tem certeza que deseja desativar o acesso de ${membership.full_name ?? membership.email}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Desativar', style: 'destructive', onPress: () => desativarMutation.mutate(membership.id) },
      ],
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Usuários</Text>
        <Pressable onPress={() => router.push('/usuarios/convidar')} style={styles.backButton} hitSlop={8}>
          <Plus size={20} color={colors.foreground} />
        </Pressable>
      </View>

      {query.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : query.isError ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar os usuários.</Text>
          <Button mode="outlined" onPress={() => query.refetch()}>
            Tentar novamente
          </Button>
        </View>
      ) : (
        <FlatList
          data={query.data ?? []}
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
          ListEmptyComponent={<Text style={styles.empty}>Nenhum usuário neste tenant.</Text>}
          renderItem={({ item }: { item: Membership }) => (
            <View style={[shared.cardSurface, styles.card]}>
              <View style={styles.cardText}>
                <Text style={styles.cardTitle}>{item.full_name ?? item.email}</Text>
                <Text style={styles.cardSubtitle}>{item.email}</Text>
                <View style={styles.badgeRow}>
                  <View style={styles.roleBadge}>
                    <Text style={styles.roleBadgeText}>{PAPEL_LABEL[item.role] ?? item.role}</Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: item.is_active ? colors.status.disponivel.soft : colors.status.indisponivel.soft }]}>
                    <View
                      style={[
                        styles.statusDot,
                        { backgroundColor: item.is_active ? colors.status.disponivel.text : colors.status.indisponivel.text },
                      ]}
                    />
                    <Text
                      style={[
                        styles.statusBadgeText,
                        { color: item.is_active ? colors.status.disponivel.text : colors.status.indisponivel.text },
                      ]}
                    >
                      {item.is_active ? 'Ativo' : 'Desativado'}
                    </Text>
                  </View>
                </View>
              </View>
              {item.is_active ? (
                <Pressable onPress={() => confirmarDesativacao(item)} hitSlop={8}>
                  <Text style={styles.desativarLink}>Desativar</Text>
                </Pressable>
              ) : null}
            </View>
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
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
  },
  roleBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: colors.muted,
  },
  roleBadgeText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusBadgeText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
  },
  desativarLink: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.destructive,
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
