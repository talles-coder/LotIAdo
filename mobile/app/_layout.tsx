import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Slot } from 'expo-router';
import { PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useFonts, Figtree_400Regular, Figtree_500Medium, Figtree_600SemiBold } from '@expo-google-fonts/figtree';
import { Outfit_600SemiBold, Outfit_700Bold } from '@expo-google-fonts/outfit';

import { initSession } from '../src/auth/session';
import { colors } from '../src/theme/tokens';
import { paperTheme } from '../src/theme/paperTheme';

export default function RootLayout() {
  const [sessionReady, setSessionReady] = useState(false);
  const [fontsLoaded] = useFonts({
    Figtree_400Regular,
    Figtree_500Medium,
    Figtree_600SemiBold,
    Outfit_600SemiBold,
    Outfit_700Bold,
  });

  useEffect(() => {
    initSession().finally(() => setSessionReady(true));
  }, []);

  if (!sessionReady || !fontsLoaded) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider theme={paperTheme}>
        <Slot />
      </PaperProvider>
    </GestureHandlerRootView>
  );
}
