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

export async function signUp(email: string, password: string, fullName?: string): Promise<AuthResponse> {
  const response = await apiClient.post("/api/v1/auth/signup", {
    email,
    password,
    full_name: fullName,
  });
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

export async function forgotPassword(email: string): Promise<void> {
  await apiClient.post("/api/v1/auth/forgot-password", { email });
}

export async function resetPassword(accessToken: string, newPassword: string): Promise<void> {
  await apiClient.post("/api/v1/auth/reset-password", {
    access_token: accessToken,
    new_password: newPassword,
  });
}

export async function resendVerification(email: string): Promise<void> {
  await apiClient.post("/api/v1/auth/resend-verification", { email });
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
