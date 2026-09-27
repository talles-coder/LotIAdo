import * as SQLite from 'expo-sqlite';

const DB_NAME = 'lotiado_cache.db';

let dbPromise: Promise<SQLite.SQLiteDatabase> | null = null;

function getDb(): Promise<SQLite.SQLiteDatabase> {
  if (!dbPromise) {
    dbPromise = SQLite.openDatabaseAsync(DB_NAME).then(async (db) => {
      await db.execAsync('CREATE TABLE IF NOT EXISTS kv_cache (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)');
      return db;
    });
  }
  return dbPromise;
}

/** Storage assíncrono compatível com `createAsyncStoragePersister`, persistido em SQLite. */
export const offlineCacheStorage = {
  async getItem(key: string): Promise<string | null> {
    const db = await getDb();
    const row = await db.getFirstAsync<{ value: string }>('SELECT value FROM kv_cache WHERE key = ?', [key]);
    return row?.value ?? null;
  },
  async setItem(key: string, value: string): Promise<void> {
    const db = await getDb();
    await db.runAsync('INSERT OR REPLACE INTO kv_cache (key, value) VALUES (?, ?)', [key, value]);
  },
  async removeItem(key: string): Promise<void> {
    const db = await getDb();
    await db.runAsync('DELETE FROM kv_cache WHERE key = ?', [key]);
  },
};

/** Apaga todo o cache offline persistido — chamado no logout para não vazar dados entre tenants no mesmo dispositivo. */
export async function clearOfflineCache(): Promise<void> {
  const db = await getDb();
  await db.execAsync('DELETE FROM kv_cache');
}
