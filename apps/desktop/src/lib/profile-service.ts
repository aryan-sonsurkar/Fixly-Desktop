import apiClient from "@/lib/api-client";
import type { Subject } from "@fixly/shared-types";

export interface ProfileData {
  id: string;
  email: string;
  full_name: string | null;
  display_name: string | null;
  avatar_url: string | null;
  education_type: string | null;
  education_year: string | null;
  college_name: string | null;
  university_board: string | null;
  branch_stream: string | null;
  division: string | null;
  roll_number: string | null;
  xp: number;
  streak: number;
  onboarding_completed: boolean;
}

export interface SettingsData {
  id: string;
  theme: string;
  daily_goal_hours: number;
  pomodoro_focus: number;
  pomodoro_break: number;
  notification_enabled: boolean;
  assignment_reminders: boolean;
  daily_briefing: boolean;
  email_monitoring: boolean;
  email_sync_enabled: boolean;
}

export async function getMyProfile(): Promise<ProfileData> {
  const response = await apiClient.get("/api/v1/profile/me");
  return response.data;
}

export async function updateMyProfile(data: Partial<ProfileData>): Promise<ProfileData> {
  const response = await apiClient.put("/api/v1/profile/me", data);
  return response.data;
}

export async function getMySettings(): Promise<SettingsData> {
  const response = await apiClient.get("/api/v1/profile/settings");
  return response.data;
}

export async function updateMySettings(data: Partial<SettingsData>): Promise<SettingsData> {
  const response = await apiClient.put("/api/v1/profile/settings", data);
  return response.data;
}

export async function completeOnboarding(data: {
  profile: Record<string, unknown>;
  settings: Record<string, unknown>;
  subjects: { name: string; color?: string }[];
}) {
  const response = await apiClient.post("/api/v1/profile/onboarding", data);
  return response.data;
}

export async function checkOnboardingStatus(): Promise<{ onboarding_completed: boolean }> {
  const response = await apiClient.get("/api/v1/profile/onboarding/status");
  return response.data;
}

export async function getSubjects(): Promise<Subject[]> {
  const response = await apiClient.get("/api/v1/subjects");
  return response.data;
}

export async function createSubject(data: {
  name: string;
  color?: string;
  icon?: string;
  credits?: number;
}): Promise<Subject> {
  const response = await apiClient.post("/api/v1/subjects", data);
  return response.data;
}

export async function updateSubject(
  id: string,
  data: Partial<{ name: string; color: string; icon: string; credits: number }>,
): Promise<Subject> {
  const response = await apiClient.put(`/api/v1/subjects/${id}`, data);
  return response.data;
}

export async function deleteSubject(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/subjects/${id}`);
}
