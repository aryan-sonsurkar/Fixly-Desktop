import { createLogger } from "@/lib/logger";

const logger = createLogger("secure-storage");

type StoreValue = string | null;

export interface AuthTokens {
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

const PROFILES_KEY = "saved_profiles";

interface StoredProfile {
  name: string;
  accessToken: string;
  refreshToken: string;
}

export interface SavedProfileSummary {
  email: string;
  name: string;
}

export async function saveProfile(email: string, name: string, tokens: AuthTokens): Promise<void> {
  try {
    const s = await getStore();
    const raw = await s.get(PROFILES_KEY);
    const profiles = raw ? (JSON.parse(raw) as Record<string, StoredProfile>) : {};
    profiles[email] = { name, accessToken: tokens.accessToken, refreshToken: tokens.refreshToken };
    await s.set(PROFILES_KEY, JSON.stringify(profiles));
    logger.debug("Profile saved");
  } catch (error) {
    logger.warn("Failed to save profile", error);
  }
}

export async function listProfiles(): Promise<SavedProfileSummary[]> {
  try {
    const s = await getStore();
    const raw = await s.get(PROFILES_KEY);
    if (!raw) return [];
    const profiles = JSON.parse(raw) as Record<string, StoredProfile>;
    return Object.entries(profiles).map(([email, p]) => ({ email, name: p.name }));
  } catch {
    return [];
  }
}

export async function restoreProfile(email: string): Promise<AuthTokens | null> {
  try {
    const s = await getStore();
    const raw = await s.get(PROFILES_KEY);
    if (!raw) return null;
    const profiles = JSON.parse(raw) as Record<string, StoredProfile>;
    const profile = profiles[email];
    if (profile && profile.accessToken && profile.refreshToken) {
      return { accessToken: profile.accessToken, refreshToken: profile.refreshToken };
    }
    return null;
  } catch {
    return null;
  }
}
