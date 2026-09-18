import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, HelperText } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { criarCliente } from '../../src/api/clientes';
import { Field } from '../../src/components/Field';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

export default function NovoClienteScreen() {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState('');
  const [documento, setDocumento] = useState('');
  const [contato, setContato] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => criarCliente({ nome: nome.trim(), documento: documento.trim(), contato: contato.trim() }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['clientes'] });
      router.back();
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível cadastrar o cliente.')),
  });

  const podeSalvar = nome.trim() !== '' && documento.trim() !== '' && contato.trim() !== '';

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Novo cliente</Text>
      </View>

      <ScrollView contentContainerStyle={styles.form} keyboardShouldPersistTaps="handled">
        <Field label="Nome completo" placeholder="Ex.: Maria Aparecida Souza" value={nome} onChangeText={setNome} />
        <Field
          label="CPF ou CNPJ"
          placeholder="000.000.000-00"
          keyboardType="numeric"
          value={documento}
          onChangeText={setDocumento}
        />
        <Field
          label="Contato"
          placeholder="(64) 99999-0000 ou cliente@email.com"
          hint="Usaremos para enviar a proposta."
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
            mutation.mutate();
          }}
          loading={mutation.isPending}
          disabled={mutation.isPending || !podeSalvar}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Salvar cliente
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
