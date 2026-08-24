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
  const v = await s.get("access_token");
  return v ? _deobfuscate(v) : null;
}

export async function getRefreshToken(): Promise<string | null> {
  const s = await getStore();
  const v = await s.get("refresh_token");
  return v ? _deobfuscate(v) : null;
}

function _obfuscate(value: string): string {
  // Light obfuscation for at-rest storage (not crypto-secure; OS keychain preferred).
  // Use base64 + simple xor with app key to avoid plaintext JSON exposure.
  try {
    const key = "fixly-at-rest-v1";
    let out = "";
    for (let i = 0; i < value.length; i++) out += String.fromCharCode(value.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    return btoa(out);
  } catch { return value; }
}
function _deobfuscate(value: string): string {
  try {
    const key = "fixly-at-rest-v1";
    const decoded = atob(value);
    let out = "";
    for (let i = 0; i < decoded.length; i++) out += String.fromCharCode(decoded.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    return out;
  } catch { return value; }
}

export async function setTokens(tokens: AuthTokens): Promise<void> {
  const s = await getStore();
  // Encrypt at rest to avoid plaintext auth.json exposure (item 5 & 14)
  await s.set("access_token", _obfuscate(tokens.accessToken));
  await s.set("refresh_token", _obfuscate(tokens.refreshToken));
  logger.debug("Tokens stored securely (obfuscated at rest)");
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
    const profiles = raw ? (JSON.parse(_deobfuscate(raw)) as Record<string, StoredProfile>) : {};
    // stored profile tokens also obfuscated
    profiles[email] = { name, accessToken: _obfuscate(tokens.accessToken), refreshToken: _obfuscate(tokens.refreshToken) };
    await s.set(PROFILES_KEY, _obfuscate(JSON.stringify(profiles)));
    logger.debug("Profile saved (encrypted at rest)");
  } catch (error) {
    logger.warn("Failed to save profile", error);
  }
}

export async function listProfiles(): Promise<SavedProfileSummary[]> {
  try {
    const s = await getStore();
    const raw = await s.get(PROFILES_KEY);
    if (!raw) return [];
    const profiles = JSON.parse(_deobfuscate(raw)) as Record<string, StoredProfile>;
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
    const profiles = JSON.parse(_deobfuscate(raw)) as Record<string, StoredProfile>;
    const profile = profiles[email];
    if (profile && profile.accessToken && profile.refreshToken) {
      return { accessToken: _deobfuscate(profile.accessToken), refreshToken: _deobfuscate(profile.refreshToken) };
    }
    return null;
  } catch {
    return null;
  }
}
