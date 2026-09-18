import { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';
import { Slot } from 'expo-router';
import { PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as SplashScreen from 'expo-splash-screen';
import { useFonts, Figtree_400Regular, Figtree_500Medium, Figtree_600SemiBold } from '@expo-google-fonts/figtree';
import { Outfit_600SemiBold, Outfit_700Bold } from '@expo-google-fonts/outfit';

import { initSession } from '../src/auth/session';
import { colors } from '../src/theme/tokens';
import { paperTheme } from '../src/theme/paperTheme';
import { SplashAnimation } from '../src/components/SplashAnimation';

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

export default function RootLayout() {
  const [sessionReady, setSessionReady] = useState(false);
  const [showLogoAnimation, setShowLogoAnimation] = useState(true);
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

  const ready = sessionReady && fontsLoaded;

  useEffect(() => {
    if (ready) {
      SplashScreen.hideAsync();
    }
  }, [ready]);

  const handleAnimationFinish = useCallback(() => setShowLogoAnimation(false), []);

  if (!ready) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <PaperProvider theme={paperTheme}>
          <View style={{ flex: 1, backgroundColor: colors.background }}>
            <Slot />
            {showLogoAnimation && <SplashAnimation onFinish={handleAnimationFinish} />}
          </View>
        </PaperProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
