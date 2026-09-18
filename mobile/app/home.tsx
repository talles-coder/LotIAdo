import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Text } from 'react-native-paper';

import { clearSession } from '../src/auth/session';
import { Logo } from '../src/components/Logo';
import { colors, fonts } from '../src/theme/tokens';

export default function HomeScreen() {
  async function handleLogout() {
    await clearSession();
    router.replace('/login');
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Logo size="sm" />
      </View>

      <View style={styles.body}>
        <Text style={styles.message}>Você está logado.</Text>
        <Button
          mode="contained"
          onPress={() => router.push('/loteamentos')}
          contentStyle={styles.logoutContent}
          labelStyle={styles.logoutLabel}
        >
          Ver loteamentos
        </Button>
        <Button
          mode="outlined"
          onPress={handleLogout}
          contentStyle={styles.logoutContent}
          labelStyle={styles.logoutLabel}
        >
          Sair
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
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 12,
  },
  body: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    padding: 24,
  },
  message: {
    fontFamily: fonts.display,
    fontSize: 18,
    color: colors.foreground,
  },
  logoutContent: {
    minHeight: 48,
    paddingHorizontal: 8,
  },
  logoutLabel: {
    fontFamily: fonts.bodySemiBold,
  },
});
