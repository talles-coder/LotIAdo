import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Text } from 'react-native-paper';

import { clearSession } from '../src/auth/session';

export default function HomeScreen() {
  async function handleLogout() {
    await clearSession();
    router.replace('/login');
  }

  return (
    <View style={styles.container}>
      <Text variant="headlineSmall">Você está logado.</Text>
      <Button mode="outlined" onPress={handleLogout} style={styles.logoutButton}>
        Sair
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  logoutButton: {
    marginTop: 16,
  },
});
