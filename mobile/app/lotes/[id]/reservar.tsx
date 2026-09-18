import { useMemo, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Button, HelperText, TextInput } from 'react-native-paper';
import { ArrowLeft, Check, Plus } from 'lucide-react-native';

import { listarClientes, type Cliente } from '../../../src/api/clientes';
import { criarReserva } from '../../../src/api/reservas';
import { getErrorMessage } from '../../../src/lib/errors';
import { colors, fonts } from '../../../src/theme/tokens';
import { shared } from '../../../src/theme/shared';

export default function ReservarLoteScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [busca, setBusca] = useState('');
  const [clienteSelecionado, setClienteSelecionado] = useState<Cliente | null>(null);
  const [error, setError] = useState<string | null>(null);

  const clientesQuery = useQuery({ queryKey: ['clientes'], queryFn: listarClientes });

  const clientesFiltrados = useMemo(() => {
    if (!clientesQuery.data) return [];
    const termo = busca.trim().toLowerCase();
    if (termo === '') return clientesQuery.data;
    return clientesQuery.data.filter(
      (cliente) =>
        cliente.nome.toLowerCase().includes(termo) || cliente.documento.toLowerCase().includes(termo),
    );
  }, [clientesQuery.data, busca]);

  const mutation = useMutation({
    mutationFn: () => criarReserva({ loteId: id, clienteId: clienteSelecionado!.id }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['lotes', id] }),
        queryClient.invalidateQueries({ queryKey: ['reservas', 'ativa-por-lote', id] }),
      ]);
      router.back();
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível reservar o lote.')),
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Reservar lote</Text>
      </View>

      <View style={styles.searchRow}>
        <TextInput
          mode="outlined"
          placeholder="Buscar cliente por nome ou documento"
          value={busca}
          onChangeText={setBusca}
          style={styles.searchInput}
          outlineStyle={styles.searchOutline}
          dense
        />
      </View>

      <Pressable
        style={styles.novoClienteRow}
        onPress={() => router.push('/clientes/novo')}
      >
        <Plus size={18} color={colors.primary} />
        <Text style={styles.novoClienteText}>Cadastrar novo cliente</Text>
      </Pressable>

      {clientesQuery.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : clientesQuery.isError ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Não foi possível carregar os clientes.</Text>
          <Button mode="outlined" onPress={() => clientesQuery.refetch()}>
            Tentar novamente
          </Button>
        </View>
      ) : (
        <FlatList
          data={clientesFiltrados}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={styles.empty}>Nenhum cliente encontrado.</Text>}
          renderItem={({ item }) => {
            const selecionado = clienteSelecionado?.id === item.id;
            return (
              <Pressable
                style={[shared.cardSurface, styles.clienteCard, selecionado && styles.clienteCardSelecionado]}
                onPress={() => setClienteSelecionado(item)}
              >
                <View style={styles.clienteInfo}>
                  <Text style={styles.clienteNome}>{item.nome}</Text>
                  <Text style={styles.clienteDocumento}>{item.documento}</Text>
                </View>
                {selecionado ? <Check size={20} color={colors.primary} /> : null}
              </Pressable>
            );
          }}
        />
      )}

      <View style={styles.footer}>
        <HelperText type="error" visible={error !== null}>
          {error}
        </HelperText>
        <Button
          mode="contained"
          onPress={() => {
            setError(null);
            mutation.mutate();
          }}
          loading={mutation.isPending}
          disabled={mutation.isPending || clienteSelecionado === null}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Confirmar reserva
        </Button>
      </View>
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
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  searchRow: {
    paddingHorizontal: 16,
  },
  searchInput: {
    backgroundColor: colors.card,
  },
  searchOutline: {
    borderRadius: 12,
  },
  novoClienteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  novoClienteText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.primary,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    gap: 8,
  },
  clienteCard: {
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  clienteCardSelecionado: {
    borderColor: colors.primary,
    borderWidth: 2,
  },
  clienteInfo: {
    flex: 1,
  },
  clienteNome: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  clienteDocumento: {
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
  footer: {
    padding: 16,
    paddingTop: 0,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
