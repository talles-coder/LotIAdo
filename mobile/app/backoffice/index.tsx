import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, Sparkles } from 'lucide-react-native';

import { obterMetricasIA, type MetricasPorOrigem } from '../../src/api/observabilidade';
import { colors, fonts, radius } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

const ORIGEM_LABEL: Record<string, string> = {
  rag: 'RAG',
  agente: 'Agente',
  importacao: 'Importação',
  desconhecida: 'Desconhecida',
};

function formatarLatencia(ms: number | null): string {
  return ms === null ? '—' : `${Math.round(ms)} ms`;
}

function formatarPercentual(fracao: number): string {
  return `${Math.round(fracao * 100)}%`;
}

export default function BackofficeMetricasScreen() {
  const query = useQuery({ queryKey: ['observabilidade', 'metricas'], queryFn: obterMetricasIA });
  const metricas = query.data;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Métricas de IA</Text>
      </View>

      {query.isError ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar as métricas.</Text>
          <Button mode="outlined" onPress={() => query.refetch()}>
            Tentar novamente
          </Button>
        </View>
      ) : !metricas ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.content}
          refreshControl={
            <RefreshControl
              refreshing={query.isRefetching}
              onRefresh={() => query.refetch()}
              colors={[colors.primary]}
              tintColor={colors.primary}
            />
          }
        >
          <View style={styles.statsRow}>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text style={styles.statValue}>{metricas.total_chamadas}</Text>
              <Text style={styles.statLabel}>Chamadas</Text>
            </View>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text
                style={[
                  styles.statValue,
                  { color: metricas.chamadas_com_erro > 0 ? colors.status.indisponivel.text : colors.status.disponivel.text },
                ]}
              >
                {formatarPercentual(metricas.taxa_erro)}
              </Text>
              <Text style={styles.statLabel}>Taxa de erro</Text>
            </View>
            <View style={[shared.cardSurface, styles.statCard]}>
              <Text style={styles.statValue}>{formatarLatencia(metricas.latencia_media_ms)}</Text>
              <Text style={styles.statLabel}>Latência média</Text>
            </View>
          </View>

          <Text style={styles.sectionTitle}>Por módulo</Text>

          {metricas.por_origem.length === 0 ? (
            <View style={[shared.cardSurface, styles.emptyCard]}>
              <Sparkles size={20} color={colors.mutedForeground} />
              <Text style={styles.emptyText}>Nenhuma chamada de IA registrada ainda.</Text>
            </View>
          ) : (
            <View style={styles.origemList}>
              {metricas.por_origem.map((item: MetricasPorOrigem) => (
                <View key={item.origem} style={[shared.cardSurface, styles.origemCard]}>
                  <View style={styles.origemHeader}>
                    <Text style={styles.origemTitulo}>{ORIGEM_LABEL[item.origem] ?? item.origem}</Text>
                    <Text style={styles.origemChamadas}>{item.total_chamadas} chamadas</Text>
                  </View>
                  <View style={styles.origemDetalhes}>
                    <Text style={styles.origemDetalheTexto}>
                      Latência média: <Text style={styles.origemDetalheValor}>{formatarLatencia(item.latencia_media_ms)}</Text>
                    </Text>
                    <Text style={styles.origemDetalheTexto}>
                      Erros:{' '}
                      <Text
                        style={[
                          styles.origemDetalheValor,
                          item.chamadas_com_erro > 0 && { color: colors.destructive },
                        ]}
                      >
                        {item.chamadas_com_erro}
                      </Text>
                    </Text>
                  </View>
                </View>
              ))}
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
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  content: {
    padding: 16,
    gap: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statCard: {
    flex: 1,
    padding: 12,
  },
  statValue: {
    fontFamily: fonts.displayBold,
    fontSize: 20,
    color: colors.foreground,
  },
  statLabel: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.mutedForeground,
    marginTop: 2,
  },
  sectionTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
    marginTop: 8,
  },
  origemList: {
    gap: 10,
  },
  origemCard: {
    padding: 14,
    gap: 8,
  },
  origemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  origemTitulo: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.foreground,
  },
  origemChamadas: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  origemDetalhes: {
    flexDirection: 'row',
    gap: 16,
  },
  origemDetalheTexto: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  origemDetalheValor: {
    fontFamily: fonts.bodySemiBold,
    color: colors.foreground,
  },
  emptyCard: {
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  emptyText: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    textAlign: 'center',
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
    textAlign: 'center',
  },
});
