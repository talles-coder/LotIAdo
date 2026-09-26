import { useEffect, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Button, HelperText } from 'react-native-paper';
import { ArrowLeft, Trash2 } from 'lucide-react-native';

import { atualizarCorretor, obterCorretor, removerCorretor } from '../../src/api/corretores';
import { Field } from '../../src/components/Field';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

export default function EditarCorretorScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['corretores', id], queryFn: () => obterCorretor(id) });

  const [nome, setNome] = useState('');
  const [contato, setContato] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.data) {
      setNome(query.data.nome);
      setContato(query.data.contato);
    }
  }, [query.data]);

  const salvarMutation = useMutation({
    mutationFn: () => atualizarCorretor(id, { nome: nome.trim(), contato: contato.trim() }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['corretores'] }),
        queryClient.invalidateQueries({ queryKey: ['corretores', id] }),
      ]);
      router.back();
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível salvar o corretor.')),
  });

  const removerMutation = useMutation({
    mutationFn: () => removerCorretor(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['corretores'] });
      router.back();
    },
    onError: (err) => Alert.alert('Não foi possível remover', getErrorMessage(err, 'Tente novamente.')),
  });

  function confirmarRemocao() {
    Alert.alert('Remover corretor', `Tem certeza que deseja remover ${nome}?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Remover', style: 'destructive', onPress: () => removerMutation.mutate() },
    ]);
  }

  const podeSalvar = nome.trim() !== '' && contato.trim() !== '';

  if (query.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {query.data?.nome ?? 'Corretor'}
        </Text>
        <Pressable onPress={confirmarRemocao} style={styles.backButton} hitSlop={8}>
          <Trash2 size={18} color={colors.destructive} />
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.form} keyboardShouldPersistTaps="handled">
        <Field label="Nome completo" placeholder="Ex.: João Pedro Almeida" value={nome} onChangeText={setNome} />
        <Field
          label="Contato"
          placeholder="(64) 99999-0000 ou corretor@email.com"
          value={contato}
          onChangeText={setContato}
        />

        <HelperText type="error" visible={error !== null}>
          {error}
        </HelperText>
      </ScrollView>

      <View style={shared.stickyFooter}>
        <Button
          mode="contained"
          onPress={() => {
            setError(null);
            salvarMutation.mutate();
          }}
          loading={salvarMutation.isPending}
          disabled={salvarMutation.isPending || !podeSalvar}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Salvar alterações
        </Button>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
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
  form: {
    flexGrow: 1,
    padding: 20,
    gap: 16,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
