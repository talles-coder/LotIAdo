import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Slot } from 'expo-router';
import { PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { initSession } from '../src/auth/session';

export default function RootLayout() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    initSession().finally(() => setReady(true));
  }, []);

  if (!ready) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <Slot />
      </PaperProvider>
    </GestureHandlerRootView>
  );
}
