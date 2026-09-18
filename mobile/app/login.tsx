import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Button, HelperText, TextInput } from 'react-native-paper';
import { isAxiosError } from 'axios';
import Svg, { Defs, Path, Pattern, Rect } from 'react-native-svg';

import { login } from '../src/api/auth';
import { setSession } from '../src/auth/session';
import { Logo } from '../src/components/Logo';
import { colors, fonts } from '../src/theme/tokens';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      const token = await login(email, password);
      await setSession(token);
      router.replace('/home');
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 401) {
        setError('E-mail ou senha inválidos.');
      } else {
        setError('Não foi possível entrar. Tente novamente.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.hero}>
        <Svg style={StyleSheet.absoluteFill} opacity={0.15}>
          <Defs>
            <Pattern id="grid" width={24} height={24} patternUnits="userSpaceOnUse">
              <Path d="M24 0H0V24" fill="none" stroke={colors.earthForeground} strokeWidth={1} />
            </Pattern>
          </Defs>
          <Rect width="100%" height="100%" fill="url(#grid)" />
        </Svg>
        <Logo size="lg" onDark />
        <Text style={styles.tagline}>Seus loteamentos, na palma da mão.</Text>
      </View>

      <ScrollView contentContainerStyle={styles.form} keyboardShouldPersistTaps="handled">
        <Text style={styles.welcome}>Bem-vindo de volta</Text>

        <TextInput
          label="E-mail"
          mode="outlined"
          autoCapitalize="none"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          outlineStyle={styles.inputOutline}
        />
        <TextInput
          label="Senha"
          mode="outlined"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          style={styles.input}
          outlineStyle={styles.inputOutline}
        />

        <HelperText type="error" visible={error !== null}>
          {error}
        </HelperText>

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={submitting}
          disabled={submitting || email === '' || password === ''}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Entrar
        </Button>

        <Text style={styles.footnote}>
          Acesso restrito a corretores e gestores cadastrados pela sua imobiliária.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: colors.background,
  },
  hero: {
    height: 224,
    backgroundColor: colors.earth,
    justifyContent: 'flex-end',
    paddingHorizontal: 24,
    paddingBottom: 32,
    overflow: 'hidden',
  },
  tagline: {
    marginTop: 12,
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.earthForeground,
    opacity: 0.8,
  },
  form: {
    flexGrow: 1,
    padding: 24,
    paddingTop: 32,
  },
  welcome: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.foreground,
    marginBottom: 20,
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
  footnote: {
    marginTop: 'auto',
    paddingTop: 24,
    textAlign: 'center',
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
});
