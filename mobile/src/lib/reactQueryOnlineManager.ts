import { onlineManager } from '@tanstack/react-query';
import NetInfo from '@react-native-community/netinfo';

/**
 * Por padrão o `onlineManager` do TanStack Query escuta `window.online`/`offline`, que nunca
 * disparam no React Native. Sem isso, queries tentariam ir à rede mesmo offline (networkMode
 * 'online' ficaria sempre "true") em vez de servir direto do cache restaurado do SQLite.
 */
export function setupReactQueryOnlineManager(): void {
  onlineManager.setEventListener((setOnline) => {
    return NetInfo.addEventListener((state) => {
      setOnline(state.isConnected === true && state.isInternetReachable !== false);
    });
  });
}
