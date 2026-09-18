import { Alert, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Button } from 'react-native-paper';
import { ArrowLeft, Check, User } from 'lucide-react-native';

import { obterCliente } from '../../src/api/clientes';
import { obterLote } from '../../src/api/loteamentos';
import {
  acoesDisponiveisParaStatus,
  cancelarReserva,
  converterReservaEmVenda,
  obterReservaAtualPorLote,
} from '../../src/api/reservas';
import { formatArea, formatBRL } from '../../src/lib/format';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';
import { StatusBadge } from '../../src/components/StatusBadge';
import { BottomNav } from '../../src/components/BottomNav';

const CELULA_DESTACADA_NA_PLANTA = 8;

export default function LoteDetalheScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['lotes', id], queryFn: () => obterLote(id) });

  const acoes = query.data ? acoesDisponiveisParaStatus(query.data.status) : null;
  const temFooterDeAcao = query.data
    ? acoes?.reservar || acoes?.converterVenda || acoes?.cancelar || query.data.status === 'vendido' || query.data.status === 'indisponivel'
    : false;

  const reservaAtualQuery = useQuery({
    queryKey: ['reservas', 'atual-por-lote', id],
    queryFn: () => obterReservaAtualPorLote(id),
    enabled: acoes?.mostrarCliente === true,
  });

  const clienteQuery = useQuery({
    queryKey: ['clientes', reservaAtualQuery.data?.cliente_id],
    queryFn: () => obterCliente(reservaAtualQuery.data!.cliente_id),
    enabled: reservaAtualQuery.data?.cliente_id !== undefined,
  });

  async function invalidarLoteEReserva() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['lotes', id] }),
      queryClient.invalidateQueries({ queryKey: ['reservas', 'atual-por-lote', id] }),
    ]);
  }

  const converterMutation = useMutation({
    mutationFn: (reservaId: string) => converterReservaEmVenda(reservaId),
    onSuccess: invalidarLoteEReserva,
    onError: (err) => Alert.alert('Não foi possível converter em venda', getErrorMessage(err, 'Tente novamente.')),
  });

  const cancelarMutation = useMutation({
    mutationFn: (reservaId: string) => cancelarReserva(reservaId),
    onSuccess: invalidarLoteEReserva,
    onError: (err) => Alert.alert('Não foi possível cancelar a reserva', getErrorMessage(err, 'Tente novamente.')),
  });

  function confirmarCancelamento(reservaId: string) {
    Alert.alert(
      'Cancelar reserva',
      'Tem certeza que deseja cancelar esta reserva? O lote voltará a ficar disponível.',
      [
        { text: 'Voltar', style: 'cancel' },
        { text: 'Cancelar reserva', style: 'destructive', onPress: () => cancelarMutation.mutate(reservaId) },
      ],
    );
  }

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

          {acoes?.mostrarCliente && (
            <View style={[shared.cardSurface, styles.section, styles.clienteCard]}>
              <User size={20} color={colors.mutedForeground} />
              <View style={styles.clienteInfo}>
                <Text style={styles.clienteLabel}>Cliente</Text>
                <Text style={styles.clienteNome}>
                  {reservaAtualQuery.isLoading || clienteQuery.isLoading
                    ? 'Carregando...'
                    : (clienteQuery.data?.nome ?? '—')}
                </Text>
              </View>
            </View>
          )}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Localização na planta</Text>
            <View style={styles.plantaGrid}>
              {Array.from({ length: 18 }).map((_, i) => (
                <View
                  key={i}
                  style={[styles.plantaCelula, i === CELULA_DESTACADA_NA_PLANTA && styles.plantaCelulaDestacada]}
                />
              ))}
            </View>
          </View>

          <Button
            mode="outlined"
            onPress={() => router.push('/clientes/novo')}
            style={styles.section}
            contentStyle={styles.actionButtonContent}
            labelStyle={styles.actionButtonLabel}
          >
            Cadastrar novo cliente
          </Button>
        </ScrollView>
      )}

      {query.data && temFooterDeAcao ? (
        <View style={shared.stickyFooter}>
          {acoes?.reservar && (
            <Button
              mode="contained"
              onPress={() => router.push(`/lotes/${id}/reservar`)}
              contentStyle={styles.actionButtonContent}
              labelStyle={styles.actionButtonLabel}
            >
              Reservar
            </Button>
          )}

          {(acoes?.converterVenda || acoes?.cancelar) &&
            (reservaAtualQuery.isLoading ? (
              <ActivityIndicator color={colors.primary} />
            ) : reservaAtualQuery.data ? (
              <View style={styles.footerActionsRow}>
                <Button
                  mode="outlined"
                  textColor={colors.destructive}
                  onPress={() => confirmarCancelamento(reservaAtualQuery.data!.id)}
                  loading={cancelarMutation.isPending}
                  disabled={converterMutation.isPending || cancelarMutation.isPending}
                  style={styles.footerActionCancelar}
                  contentStyle={styles.footerActionContent}
                  labelStyle={styles.footerActionLabel}
                >
                  Cancelar reserva
                </Button>
                <Button
                  mode="contained"
                  buttonColor={colors.accent}
                  icon={({ size, color }) => <Check size={size} color={color} />}
                  onPress={() => converterMutation.mutate(reservaAtualQuery.data!.id)}
                  loading={converterMutation.isPending}
                  disabled={converterMutation.isPending || cancelarMutation.isPending}
                  style={styles.footerActionConverter}
                  contentStyle={styles.footerActionContent}
                  labelStyle={styles.footerActionLabel}
                >
                  Converter em venda
                </Button>
              </View>
            ) : (
              <Text style={styles.errorText}>Não foi possível carregar a reserva deste lote.</Text>
            ))}

          {query.data.status === 'vendido' && (
            <View style={[styles.infoBanner, { backgroundColor: colors.status.vendido.soft }]}>
              <Check size={18} color={colors.status.vendido.text} />
              <Text style={[styles.infoBannerText, { color: colors.status.vendido.text }]}>
                Venda concluída — nenhuma ação disponível
              </Text>
            </View>
          )}

          {query.data.status === 'indisponivel' && (
            <View style={[styles.infoBanner, { backgroundColor: colors.status.indisponivel.soft }]}>
              <Text style={[styles.infoBannerText, { color: colors.status.indisponivel.text }]}>
                Lote indisponível — fale com o gestor.
              </Text>
            </View>
          )}
        </View>
      ) : (
        <BottomNav />
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
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  body: {
    padding: 20,
    paddingTop: 16,
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
  clienteCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
  },
  clienteInfo: {
    flex: 1,
  },
  clienteLabel: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  clienteNome: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.foreground,
    marginTop: 2,
  },
  plantaGrid: {
    marginTop: 8,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    backgroundColor: colors.muted,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 8,
  },
  plantaCelula: {
    width: '15%',
    aspectRatio: 1,
    backgroundColor: colors.card,
    borderRadius: 6,
  },
  plantaCelulaDestacada: {
    backgroundColor: colors.primary,
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
  actionButtonContent: {
    minHeight: 48,
  },
  actionButtonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 15,
  },
  footerActionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  footerActionCancelar: {
    flex: 1,
  },
  footerActionConverter: {
    flex: 1.4,
  },
  footerActionContent: {
    minHeight: 48,
    paddingHorizontal: 2,
  },
  footerActionLabel: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    marginHorizontal: 4,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    minHeight: 48,
    borderRadius: 10,
    paddingHorizontal: 16,
  },
  infoBannerText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    textAlign: 'center',
  },
});
