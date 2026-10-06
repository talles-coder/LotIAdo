const PREFIX = 'lotiado_cache:';

/** Storage assíncrono compatível com `createAsyncStoragePersister`, persistido em `localStorage` (web). */
export const offlineCacheStorage = {
  async getItem(key: string): Promise<string | null> {
    return localStorage.getItem(PREFIX + key);
  },
  async setItem(key: string, value: string): Promise<void> {
    localStorage.setItem(PREFIX + key, value);
  },
  async removeItem(key: string): Promise<void> {
    localStorage.removeItem(PREFIX + key);
  },
};

/** Apaga todo o cache offline persistido — chamado no logout para não vazar dados entre tenants no mesmo dispositivo. */
export async function clearOfflineCache(): Promise<void> {
  Object.keys(localStorage)
    .filter((key) => key.startsWith(PREFIX))
    .forEach((key) => localStorage.removeItem(key));
}
