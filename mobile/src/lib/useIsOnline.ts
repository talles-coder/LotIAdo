import { useSyncExternalStore } from 'react';
import NetInfo, { type NetInfoState } from '@react-native-community/netinfo';

type Listener = () => void;

export const OFFLINE_MESSAGE = 'Conecte-se à internet para editar.';

let isOnline = true;
const listeners = new Set<Listener>();
let unsubscribeNetInfo: (() => void) | null = null;

function computeIsOnline(state: NetInfoState): boolean {
  return state.isConnected === true && state.isInternetReachable !== false;
}

function notify() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: Listener): () => void {
  if (listeners.size === 0) {
    unsubscribeNetInfo = NetInfo.addEventListener((state) => {
      isOnline = computeIsOnline(state);
      notify();
    });
  }
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && unsubscribeNetInfo) {
      unsubscribeNetInfo();
      unsubscribeNetInfo = null;
    }
  };
}

function getSnapshot(): boolean {
  return isOnline;
}

/** Re-renders the calling component whenever device connectivity changes; starts optimistic (online) until NetInfo reports otherwise. */
export function useIsOnline(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot);
}
