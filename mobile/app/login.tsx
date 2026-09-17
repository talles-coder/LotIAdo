import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { Button, HelperText, Text, TextInput } from 'react-native-paper';
import { isAxiosError } from 'axios';

import { login } from '../src/api/auth';
import { setSession } from '../src/auth/session';

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
    <View style={styles.container}>
      <Text variant="headlineMedium" style={styles.title}>
        Hope
      </Text>

      <TextInput
        label="E-mail"
        mode="outlined"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={styles.input}
      />
      <TextInput
        label="Senha"
        mode="outlined"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={styles.input}
      />

      <HelperText type="error" visible={error !== null}>
        {error}
      </HelperText>

      <Button
        mode="contained"
        onPress={handleSubmit}
        loading={submitting}
        disabled={submitting || email === '' || password === ''}
      >
        Entrar
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    marginBottom: 32,
    textAlign: 'center',
  },
  input: {
    marginBottom: 8,
  },
});
