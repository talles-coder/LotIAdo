import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, HelperText, TextInput } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { criarCliente } from '../../src/api/clientes';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';

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
        <TextInput
          label="Nome"
          mode="outlined"
          value={nome}
          onChangeText={setNome}
          style={styles.input}
          outlineStyle={styles.inputOutline}
        />
        <TextInput
          label="Documento (CPF/CNPJ)"
          mode="outlined"
          value={documento}
          onChangeText={setDocumento}
          style={styles.input}
          outlineStyle={styles.inputOutline}
        />
        <TextInput
          label="Contato (e-mail ou telefone)"
          mode="outlined"
          value={contato}
          onChangeText={setContato}
          style={styles.input}
          outlineStyle={styles.inputOutline}
        />

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
          disabled={mutation.isPending || !podeSalvar}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Cadastrar cliente
        </Button>
      </ScrollView>
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
    paddingTop: 8,
  },
  input: {
    marginBottom: 12,
    backgroundColor: colors.card,
  },
  inputOutline: {
    borderRadius: 12,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
