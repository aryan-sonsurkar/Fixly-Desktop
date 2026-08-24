import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import { AxiosError } from "axios";
import { useAuthStore, type AuthUser } from "@/stores/auth-store";
import { setTokens, clearTokens, restoreSession, saveProfile, type AuthTokens } from "@/lib/secure-storage";
import apiClient, { ensureApiReady } from "@/lib/api-client";
import { createLogger } from "@/lib/logger";

const logger = createLogger("auth-context");

// A 4xx response means the server actively rejected the credentials (invalid or
// expired token) — the correct time to wipe a session. Network errors and 5xx
// are transient (backend still starting, one-off blip) and must never destroy
// stored tokens, otherwise every launch that races the backend boot force-logs
// the user out.
function isDefinitiveAuthRejection(error: unknown): boolean {
  return error instanceof AxiosError && !!error.response && error.response.status >= 400 && error.response.status < 500;
}

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password?: string, fullName?: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function isAuthDeepLink(url: URL): boolean {
  return (
    url.pathname === "/auth/callback" ||
    url.pathname === "/auth/verified" ||
    (url.protocol === "fixly:" && url.host === "auth" && (url.pathname === "/callback" || url.pathname === "/verified"))
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  const persistSession = useCallback((email: string, name: string, tokens: AuthTokens) => {
    setTokens(tokens);
    void saveProfile(email, name, tokens);
  }, []);

  const handleAuthResponse = useCallback(
    (data: { access_token: string; refresh_token: string; user: AuthUser }) => {
      setAuth(data.access_token, data.user);
      const profile = data.user.profile as Record<string, unknown> | null | undefined;
      const metadata = data.user.user_metadata as Record<string, unknown> | null | undefined;
      const displayName =
        (profile && typeof profile.full_name === "string" ? profile.full_name : "") ||
        (metadata && typeof metadata.full_name === "string" ? metadata.full_name : "") ||
        data.user.email;
      persistSession(data.user.email, displayName, {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });
    },
    [setAuth, persistSession],
  );

  const signIn = useCallback(
    async (email: string, password: string) => {
      const response = await apiClient.post("/api/v1/auth/signin", { email, password });
      handleAuthResponse(response.data);
    },
    [handleAuthResponse],
  );

  const signUp = useCallback(
    async (email: string, password?: string, fullName?: string) => {
      const body: Record<string, unknown> = { email, full_name: fullName };
      if (password) body.password = password;
      const response = await apiClient.post("/api/v1/auth/signup", body);
      handleAuthResponse(response.data);
    },
    [handleAuthResponse],
  );

  const signOut = useCallback(async () => {
    try {
      await apiClient.post("/api/v1/auth/signout");
    } catch {
      // Proceed with local signout even if API call fails
    }
    clearAuth();
    await clearTokens();
  }, [clearAuth]);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const tokens = await restoreSession();
      if (!tokens) return false;

      // Wait for the API client to target the real backend port before making
      // the refresh call. During cold start the auth effect can otherwise fire
      // before the Tauri adapter is installed, hitting the default port and
      // failing with a network error.
      await ensureApiReady();

      const response = await apiClient.post("/api/v1/auth/refresh", {
        refresh_token: tokens.refreshToken,
      });
      handleAuthResponse(response.data);
      logger.info("Session refreshed successfully");
      return true;
    } catch (error) {
      logger.error("Session refresh failed", error);
      // Only wipe when the server definitively rejected the refresh token.
      // Keep the tokens on transient failures so a cold-start race doesn't
      // permanently log the user out.
      if (isDefinitiveAuthRejection(error)) {
        clearAuth();
        await clearTokens();
      }
      return false;
    }
  }, [handleAuthResponse, clearAuth]);

  // Handle deep links for authentication (OAuth callbacks, email verification, etc.)
  useEffect(() => {
    let unlisten: (() => void) | null = null;

    const setupDeepLinkListener = async () => {
      const tauriWindow = typeof window !== "undefined" ? (window as { __TAURI__?: unknown; __TAURI_INTERNALS__?: unknown }) : null;
      if (tauriWindow?.__TAURI__ || tauriWindow?.__TAURI_INTERNALS__) {
        try {
          const { getCurrent, onOpenUrl } = await import("@tauri-apps/plugin-deep-link");
          const { googleCallback } = await import("@/lib/auth-service");

          const urlToString = (value: unknown): string => {
            if (typeof value === "string") return value;
            if (value instanceof URL) return value.href;
            if (Array.isArray(value) && value.length > 0) return urlToString(value[0]);
            return String(value);
          };

          const handleDeepLink = async (uri: string) => {
            logger.info("Deep link received:", uri);

            try {
              const url = new URL(uri);

              if (isAuthDeepLink(url)) {
                const code = url.searchParams.get("code");
                const accessToken = url.searchParams.get("access_token") || url.hash.split("access_token=")[1]?.split("&")[0];
                const refreshToken = url.searchParams.get("refresh_token") || url.hash.split("refresh_token=")[1]?.split("&")[0];
                const token = url.searchParams.get("token");

                if (code) {
                  const response = await googleCallback(code, "fixly://auth/callback");
                  handleAuthResponse(response);
                  logger.info("Google OAuth authentication successful via deep link");
                } else if (accessToken && refreshToken) {
                  const response = await apiClient.get("/api/v1/auth/me", {
                    headers: { Authorization: `Bearer ${accessToken}` },
                  });
                  handleAuthResponse({ access_token: accessToken, refresh_token: refreshToken, user: response.data });
                  logger.info("OAuth authentication successful via deep link");
                } else if (token) {
                  logger.info("Email verification callback received");
                  await refreshSession();
                }
              }
            } catch (error) {
              logger.error("Failed to handle deep link:", error);
            }
          };

          unlisten = await onOpenUrl((payload: unknown) => {
            void handleDeepLink(urlToString(payload));
          });

          const current = await getCurrent();
          if (current && current.length > 0) {
            void handleDeepLink(urlToString(current[0]));
          }
        } catch (error) {
          logger.error("Failed to set up deep link listener:", error);
        }
      }
    };

    void setupDeepLinkListener();

    return () => {
      if (unlisten) unlisten();
    };
  }, [handleAuthResponse, refreshSession]);

  useEffect(() => {
    const handleAuthExpired = () => {
      clearAuth();
      void clearTokens();
    };
    window.addEventListener("fixly:auth-expired", handleAuthExpired);
    return () => {
      window.removeEventListener("fixly:auth-expired", handleAuthExpired);
    };
  }, [clearAuth]);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setIsLoading(true);
      const tokens = await restoreSession();
      if (!tokens) {
        if (!cancelled) setIsLoading(false);
        return;
      }
      const success = await refreshSession();
      if (success) {
        if (!cancelled) setIsLoading(false);
        return;
      }
      try {
        await ensureApiReady();
        const response = await apiClient.get("/api/v1/auth/me", {
          headers: { Authorization: `Bearer ${tokens.accessToken}` },
        });
        if (!cancelled) {
          setAuth(tokens.accessToken, response.data);
          setIsLoading(false);
        }
      } catch (error) {
        logger.warn("Restore via access token failed", error);
        // Never wipe the stored refresh token here: an expired access token is
        // expected, and the refresh token may still be valid for a later
        // attempt. Wiping on this path could permanently log the user out.
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }
    init();
    return () => { cancelled = true; };
  }, [refreshSession, setAuth, clearAuth]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        signIn,
        signUp,
        signOut,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within AuthProvider");
  return ctx;
}
