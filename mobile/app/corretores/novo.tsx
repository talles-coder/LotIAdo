import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, HelperText } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { criarCorretor } from '../../src/api/corretores';
import { Field } from '../../src/components/Field';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

export default function NovoCorretorScreen() {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState('');
  const [contato, setContato] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => criarCorretor({ nome: nome.trim(), contato: contato.trim() }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['corretores'] });
      router.back();
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível cadastrar o corretor.')),
  });

  const podeSalvar = nome.trim() !== '' && contato.trim() !== '';

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Novo corretor</Text>
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
            mutation.mutate();
          }}
          loading={mutation.isPending}
          disabled={mutation.isPending || !podeSalvar}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Salvar corretor
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
