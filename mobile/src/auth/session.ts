import { useSyncExternalStore } from 'react';

import { clearToken, getToken, setToken } from '../storage/tokenStorage';

type Listener = () => void;

let token: string | null = null;
const listeners = new Set<Listener>();

function notify() {
  listeners.forEach((listener) => listener());
}

/** Reads the persisted token once at app start so a reopened app resumes its session. */
export async function initSession(): Promise<void> {
  token = await getToken();
  notify();
}

export function getSessionToken(): string | null {
  return token;
}

export async function setSession(newToken: string): Promise<void> {
  token = newToken;
  await setToken(newToken);
  notify();
}

export async function clearSession(): Promise<void> {
  token = null;
  await clearToken();
  notify();
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Re-renders the calling component whenever the session token changes. */
export function useSession(): string | null {
  return useSyncExternalStore(subscribe, getSessionToken);
}
