import { createLogger } from "@/lib/logger";

const logger = createLogger("secure-storage");

type StoreValue = string | null;

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

let store: { get: (key: string) => Promise<StoreValue>; set: (key: string, value: string) => Promise<void>; delete: (key: string) => Promise<void> } | null = null;

async function getStore() {
  if (store) return store;
  try {
    const { load } = await import("@tauri-apps/plugin-store");
    const s = await load("auth.json", { autoSave: true, defaults: {} });
    store = {
      get: async (key: string) => {
        const val = await s.get<string>(key);
        return val ?? null;
      },
      set: async (key: string, value: string) => {
        await s.set(key, value);
        await s.save();
      },
      delete: async (key: string) => {
        await s.delete(key);
        await s.save();
      },
    };
    return store;
  } catch {
    logger.warn("Tauri store unavailable, falling back to memory");
    const mem = new Map<string, string>();
    store = {
      get: async (key: string) => mem.get(key) ?? null,
      set: async (key: string, value: string) => { mem.set(key, value); },
      delete: async (key: string) => { mem.delete(key); },
    };
    return store;
  }
}

export async function getAccessToken(): Promise<string | null> {
  const s = await getStore();
  return s.get("access_token");
}

export async function getRefreshToken(): Promise<string | null> {
  const s = await getStore();
  return s.get("refresh_token");
}

export async function setTokens(tokens: AuthTokens): Promise<void> {
  const s = await getStore();
  await s.set("access_token", tokens.accessToken);
  await s.set("refresh_token", tokens.refreshToken);
  logger.debug("Tokens stored securely");
}

export async function clearTokens(): Promise<void> {
  const s = await getStore();
  await s.delete("access_token");
  await s.delete("refresh_token");
  logger.debug("Tokens cleared");
}

export async function restoreSession(): Promise<AuthTokens | null> {
  const accessToken = await getAccessToken();
  const refreshToken = await getRefreshToken();
  if (accessToken && refreshToken) {
    logger.debug("Session restored from secure storage");
    return { accessToken, refreshToken };
  }
  return null;
}
