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
