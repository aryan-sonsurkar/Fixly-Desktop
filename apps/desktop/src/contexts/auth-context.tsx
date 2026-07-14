import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import { useAuthStore, type AuthUser } from "@/stores/auth-store";
import { setTokens, clearTokens, restoreSession } from "@/lib/secure-storage";
import apiClient from "@/lib/api-client";
import { createLogger } from "@/lib/logger";

const logger = createLogger("auth-context");

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  const handleAuthResponse = useCallback(
    (data: { access_token: string; refresh_token: string; user: AuthUser }) => {
      setAuth(data.access_token, data.user);
      setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
    },
    [setAuth],
  );

  const signIn = useCallback(
    async (email: string, password: string) => {
      const response = await apiClient.post("/api/v1/auth/signin", { email, password });
      handleAuthResponse(response.data);
    },
    [handleAuthResponse],
  );

  const signUp = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const response = await apiClient.post("/api/v1/auth/signup", {
        email,
        password,
        full_name: fullName,
      });
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

      const response = await apiClient.post("/api/v1/auth/refresh", {
        refresh_token: tokens.refreshToken,
      });
      handleAuthResponse(response.data);
      logger.info("Session refreshed successfully");
      return true;
    } catch (error) {
      logger.error("Session refresh failed", error);
      clearAuth();
      await clearTokens();
      return false;
    }
  }, [handleAuthResponse, clearAuth]);

  // Handle deep links for authentication (OAuth callbacks, email verification, etc.)
  useEffect(() => {
    let unlisten: (() => void) | null = null;
    
    const setupDeepLinkListener = async () => {
      if (typeof window !== "undefined" && (window as { __TAURI__?: unknown }).__TAURI__) {
        try {
          const { listen } = await import("@tauri-apps/api/event");
          unlisten = await listen("deep-link", async (event: { payload: string }) => {
            const uri = event.payload;
            logger.info("Deep link received:", uri);
            
            try {
              const url = new URL(uri);
              
              if (url.pathname === "/auth/callback" || url.pathname === "/auth/verified") {
                const accessToken = url.searchParams.get("access_token") || url.hash.split("access_token=")[1]?.split("&")[0];
                const refreshToken = url.searchParams.get("refresh_token") || url.hash.split("refresh_token=")[1]?.split("&")[0];
                const token = url.searchParams.get("token");
                
                if (accessToken && refreshToken) {
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
          });
        } catch (error) {
          logger.error("Failed to set up deep link listener:", error);
        }
      }
    };
    
    setupDeepLinkListener();
    
    return () => {
      if (unlisten) unlisten();
    };
  }, [handleAuthResponse, refreshSession]);

  useEffect(() => {
    async function init() {
      setIsLoading(true);
      const tokens = await restoreSession();
      if (!tokens) {
        setIsLoading(false);
        return;
      }
      const success = await refreshSession();
      if (!success) {
        try {
          const response = await apiClient.get("/api/v1/auth/me", {
            headers: { Authorization: `Bearer ${tokens.accessToken}` },
          });
          setAuth(tokens.accessToken, response.data);
        } catch {
          await clearTokens();
          clearAuth();
        }
      }
      setIsLoading(false);
    }
    init();
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
