import { create } from "zustand";
import type { User } from "@fixly/shared-types";

interface AuthUser {
  id: string;
  email: string;
  profile?: User | null;
  user_metadata?: Record<string, unknown> | null;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  clearAuth: () => void;
  setUser: (user: AuthUser) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
  clearAuth: () => set({ token: null, user: null, isAuthenticated: false }),
  setUser: (user) => set({ user }),
}));

export type { AuthUser };
