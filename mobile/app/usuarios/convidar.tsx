import { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, HelperText } from 'react-native-paper';
import { ArrowLeft } from 'lucide-react-native';

import { convidarUsuario, type PapelUsuario } from '../../src/api/usuarios';
import { Field } from '../../src/components/Field';
import { getErrorMessage } from '../../src/lib/errors';
import { colors, fonts } from '../../src/theme/tokens';
import { shared } from '../../src/theme/shared';

const PAPEIS: { key: PapelUsuario; label: string }[] = [
  { key: 'corretor', label: 'Corretor' },
  { key: 'gestor', label: 'Gestor' },
  { key: 'admin', label: 'Admin' },
];

export default function ConvidarUsuarioScreen() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<PapelUsuario>('corretor');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => convidarUsuario({ email: email.trim(), role }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['usuarios', 'memberships'] });
      Alert.alert('Convite enviado', `${email.trim()} foi convidado como ${role}.`);
      router.back();
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível enviar o convite.')),
  });

  const podeConvidar = email.trim() !== '';

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Convidar usuário</Text>
      </View>

      <ScrollView contentContainerStyle={styles.form} keyboardShouldPersistTaps="handled">
        <Field
          label="E-mail"
          placeholder="pessoa@email.com"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
        />

        <View style={styles.roleWrap}>
          <Text style={styles.roleLabel}>Papel</Text>
          <View style={styles.roleRow}>
            {PAPEIS.map((papel) => {
              const active = role === papel.key;
              return (
                <Pressable
                  key={papel.key}
                  onPress={() => setRole(papel.key)}
                  style={[styles.roleChip, active && styles.roleChipActive]}
                >
                  <Text style={[styles.roleChipText, active && styles.roleChipTextActive]}>{papel.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

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
          disabled={mutation.isPending || !podeConvidar}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Enviar convite
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
  roleWrap: {
    gap: 6,
  },
  roleLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.foreground,
  },
  roleRow: {
    flexDirection: 'row',
    gap: 8,
  },
  roleChip: {
    height: 36,
    paddingHorizontal: 16,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  roleChipText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
  roleChipTextActive: {
    color: colors.primaryForeground,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
