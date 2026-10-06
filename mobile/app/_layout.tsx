import { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';
import { Slot } from 'expo-router';
import { PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient } from '@tanstack/react-query';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import * as SplashScreen from 'expo-splash-screen';
import { useFonts, Figtree_400Regular, Figtree_500Medium, Figtree_600SemiBold } from '@expo-google-fonts/figtree';
import { Outfit_600SemiBold, Outfit_700Bold } from '@expo-google-fonts/outfit';

import { initSession } from '../src/auth/session';
import { offlineCacheStorage } from '../src/storage/offlineCache';
import { setupReactQueryOnlineManager } from '../src/lib/reactQueryOnlineManager';
import { colors } from '../src/theme/tokens';
import { paperTheme } from '../src/theme/paperTheme';
import { SplashAnimation } from '../src/components/SplashAnimation';
import { WebShell } from '../src/components/WebShell';

SplashScreen.preventAutoHideAsync();
setupReactQueryOnlineManager();

const queryClient = new QueryClient();
const persister = createAsyncStoragePersister({ storage: offlineCacheStorage });

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
      <PersistQueryClientProvider client={queryClient} persistOptions={{ persister }}>
        <PaperProvider theme={paperTheme}>
          <View style={{ flex: 1, backgroundColor: colors.background }}>
            <WebShell>
              <Slot />
            </WebShell>
            {showLogoAnimation && <SplashAnimation onFinish={handleAnimationFinish} />}
          </View>
        </PaperProvider>
      </PersistQueryClientProvider>
    </GestureHandlerRootView>
  );
}
