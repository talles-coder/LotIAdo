import { useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useQueries, useQuery } from '@tanstack/react-query';
import { ActivityIndicator } from 'react-native-paper';
import { ChevronRight, LogOut, MapPin, Sparkles, UserCog, Users } from 'lucide-react-native';

import { clearSession } from '../src/auth/session';
import { obterUsuarioAtual } from '../src/api/auth';
import { listarLoteamentos, listarLotes } from '../src/api/loteamentos';
import { saudacao } from '../src/lib/greeting';
import { Logo } from '../src/components/Logo';
import { BottomNav } from '../src/components/BottomNav';
import { colors, fonts } from '../src/theme/tokens';
import { shared } from '../src/theme/shared';

export default function HomeScreen() {
  const meQuery = useQuery({ queryKey: ['auth', 'me'], queryFn: obterUsuarioAtual });
  const loteamentosQuery = useQuery({ queryKey: ['loteamentos'], queryFn: listarLoteamentos });
  const loteamentos = loteamentosQuery.data ?? [];

  // Mesma queryKey da lista de loteamentos e da lista de lotes — reaproveita cache entre telas.
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

  const totais = useMemo(() => {
    const todosLotes = lotesQueries.flatMap((q) => q.data ?? []);
    return {
      disponiveis: todosLotes.filter((l) => l.status === 'disponivel').length,
      reservados: todosLotes.filter((l) => l.status === 'reservado').length,
      vendidos: todosLotes.filter((l) => l.status === 'vendido').length,
    };
  }, [lotesQueries]);

  const nome = meQuery.data?.full_name?.split(' ')[0] ?? meQuery.data?.email.split('@')[0] ?? '';

  async function handleLogout() {
    await clearSession();
    router.replace('/login');
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <Logo size="sm" />
          <Pressable onPress={handleLogout} style={styles.iconButton} hitSlop={8}>
            <LogOut size={20} color={colors.mutedForeground} />
          </Pressable>
        </View>

        <View style={styles.greeting}>
          <Text style={styles.greetingLabel}>{saudacao()}</Text>
          <Text style={styles.greetingName}>{nome || ' '}</Text>
        </View>

        {loteamentosQuery.isLoading ? (
          <ActivityIndicator style={styles.loadingStats} color={colors.primary} />
        ) : (
          <View style={styles.statsRow}>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text style={[styles.statValue, { color: colors.status.disponivel.text }]}>{totais.disponiveis}</Text>
              <Text style={styles.statLabel}>Disponíveis</Text>
            </View>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text style={[styles.statValue, { color: colors.status.reservado.text }]}>{totais.reservados}</Text>
              <Text style={styles.statLabel}>Reservados</Text>
            </View>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text style={[styles.statValue, { color: colors.status.vendido.text }]}>{totais.vendidos}</Text>
              <Text style={styles.statLabel}>Vendidos</Text>
            </View>
          </View>
        )}

        <View style={styles.aiBanner}>
          <View style={styles.aiIconWrap}>
            <Sparkles size={20} color={colors.accentForeground} />
          </View>
          <View style={styles.aiTextWrap}>
            <Text style={styles.aiTitle}>Pergunte ao LotIAdo</Text>
            <Text style={styles.aiSubtitle}>"Quais lotes de esquina abaixo de 100 mil?"</Text>
          </View>
          <ChevronRight size={18} color={colors.earthForeground} style={{ opacity: 0.7 }} />
        </View>
        <Text style={styles.aiComingSoon}>Em breve — assistente de IA (Fase 7)</Text>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Loteamentos recentes</Text>
          <Pressable onPress={() => router.push('/loteamentos')}>
            <Text style={styles.sectionLink}>Ver todos</Text>
          </Pressable>
        </View>

        {loteamentosQuery.isLoading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <View style={styles.recentList}>
            {loteamentos.slice(0, 3).map((l) => {
              const disponibilidade = disponibilidadePorLoteamento.get(l.id);
              return (
                <Pressable
                  key={l.id}
                  style={({ pressed }) => [shared.cardSurface, styles.recentCard, pressed && styles.recentCardPressed]}
                  onPress={() => router.push(`/loteamentos/${l.id}`)}
                >
                  <View style={styles.recentCardText}>
                    <Text style={styles.recentTitle}>{l.nome}</Text>
                    {l.descricao ? (
                      <View style={styles.recentLocation}>
                        <MapPin size={12} color={colors.mutedForeground} />
                        <Text style={styles.recentSubtitle}>{l.descricao}</Text>
                      </View>
                    ) : null}
                  </View>
                  {disponibilidade ? (
                    <View style={styles.recentStat}>
                      <Text style={styles.recentStatValue}>{disponibilidade.disponiveis}</Text>
                      <Text style={styles.recentStatLabel}>de {disponibilidade.total}</Text>
                    </View>
                  ) : null}
                  <ChevronRight size={18} color={colors.mutedForeground} />
                </Pressable>
              );
            })}
          </View>
        )}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Gestão</Text>
        </View>

        <View style={styles.recentList}>
          <Pressable
            style={({ pressed }) => [shared.cardSurface, styles.recentCard, pressed && styles.recentCardPressed]}
            onPress={() => router.push('/corretores')}
          >
            <View style={styles.gestaoIconWrap}>
              <Users size={18} color={colors.mutedForeground} />
            </View>
            <View style={styles.recentCardText}>
              <Text style={styles.recentTitle}>Corretores</Text>
            </View>
            <ChevronRight size={18} color={colors.mutedForeground} />
          </Pressable>
          <Pressable
            style={({ pressed }) => [shared.cardSurface, styles.recentCard, pressed && styles.recentCardPressed]}
            onPress={() => router.push('/usuarios')}
          >
            <View style={styles.gestaoIconWrap}>
              <UserCog size={18} color={colors.mutedForeground} />
            </View>
            <View style={styles.recentCardText}>
              <Text style={styles.recentTitle}>Usuários</Text>
            </View>
            <ChevronRight size={18} color={colors.mutedForeground} />
          </Pressable>
        </View>
      </ScrollView>

      <BottomNav />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scroll: {
    padding: 20,
    paddingBottom: 28,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  greeting: {
    marginTop: 20,
  },
  greetingLabel: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
  },
  greetingName: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.foreground,
    marginTop: 2,
  },
  loadingStats: {
    marginTop: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 20,
  },
  statCard: {
    flex: 1,
    padding: 12,
  },
  statValue: {
    fontFamily: fonts.displayBold,
    fontSize: 22,
  },
  statLabel: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.mutedForeground,
    marginTop: 2,
  },
  aiBanner: {
    marginTop: 16,
    borderRadius: 16,
    backgroundColor: colors.earth,
    paddingHorizontal: 16,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  aiIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiTextWrap: {
    flex: 1,
  },
  aiTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.earthForeground,
  },
  aiSubtitle: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.earthForeground,
    opacity: 0.75,
    marginTop: 2,
  },
  aiComingSoon: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.mutedForeground,
    marginTop: 6,
    marginLeft: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginTop: 24,
  },
  sectionTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  sectionLink: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primary,
  },
  recentList: {
    marginTop: 12,
    gap: 10,
  },
  recentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 14,
  },
  recentCardPressed: {
    backgroundColor: colors.muted,
  },
  recentCardText: {
    flex: 1,
  },
  recentTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.foreground,
  },
  recentLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  recentSubtitle: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  recentStat: {
    alignItems: 'flex-end',
  },
  gestaoIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.muted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recentStatValue: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
    color: colors.status.disponivel.text,
  },
  recentStatLabel: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.mutedForeground,
  },
});
