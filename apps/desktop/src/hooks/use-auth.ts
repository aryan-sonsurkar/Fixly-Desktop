import { useAuthContext } from "@/contexts/auth-context";

export function useAuth() {
  return useAuthContext();
}

export function useIsAuthenticated() {
  const { isAuthenticated, isLoading } = useAuthContext();
  return { isAuthenticated, isLoading };
}

export function useUser() {
  const { user, isLoading } = useAuthContext();
  return { user, isLoading };
}
