import apiClient from "@/lib/api-client";
import type { AuthUser } from "@/stores/auth-store";

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export async function signIn(email: string, password: string): Promise<AuthResponse> {
  const response = await apiClient.post("/api/v1/auth/signin", { email, password });
  return response.data;
}

export async function signUp(email: string, password?: string, fullName?: string): Promise<AuthResponse> {
  const body: Record<string, unknown> = { email, full_name: fullName };
  if (password) body.password = password;
  const response = await apiClient.post("/api/v1/auth/signup", body);
  return response.data;
}

export async function signOut(): Promise<void> {
  await apiClient.post("/api/v1/auth/signout");
}

export async function refreshToken(refresh_token: string): Promise<AuthResponse> {
  const response = await apiClient.post("/api/v1/auth/refresh", { refresh_token });
  return response.data;
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get("/api/v1/auth/me");
  return response.data;
}

export async function getGoogleAuthUrl(): Promise<string> {
  const response = await apiClient.get("/api/v1/auth/google/url");
  return response.data.url;
}

export async function googleCallback(code: string, redirectUri: string): Promise<AuthResponse> {
  const response = await apiClient.post("/api/v1/auth/google/callback", {
    code,
    redirect_uri: redirectUri,
  });
  return response.data;
}
