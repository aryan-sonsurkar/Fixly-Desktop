import apiClient from "@/lib/api-client";

export interface PomodoroSettingsData {
  focus_duration: number;
  short_break_duration: number;
  long_break_duration: number;
  long_break_interval: number;
  daily_goal: number;
  auto_start_breaks: boolean;
  auto_start_focus: boolean;
  sound_enabled: boolean;
  ticking_sound: boolean;
  desktop_notifications: boolean;
}

export interface PomodoroSessionData {
  id: string;
  user_id: string;
  focus_duration: number;
  break_duration: number;
  cycles_completed: number;
  total_focus_minutes: number;
  interruptions: number;
  tags: string[];
  notes: string | null;
  mood_after: string | null;
  subject_id: string | null;
  daily_goal_progress: number;
  date: string;
  created_at: string;
}

export interface PomodoroAnalyticsData {
  total_sessions: number;
  total_focus_minutes: number;
  total_cycles: number;
  average_focus_minutes: number;
  current_streak: number;
  longest_streak: number;
  daily_goal_progress: number;
  weekly_data: Array<{ date: string; minutes: number }>;
  monthly_data: Array<{ date: string; minutes: number }>;
}

export async function getPomodoroSettings(): Promise<PomodoroSettingsData> {
  const response = await apiClient.get("/api/v1/pomodoro/settings");
  return response.data;
}

export async function updatePomodoroSettings(
  settings: Partial<PomodoroSettingsData>,
): Promise<PomodoroSettingsData> {
  const response = await apiClient.put("/api/v1/pomodoro/settings", settings);
  return response.data;
}

export async function completePomodoroSession(
  session: Omit<
    PomodoroSessionData,
    "id" | "user_id" | "daily_goal_progress" | "date" | "created_at"
  >,
): Promise<PomodoroSessionData> {
  const response = await apiClient.post("/api/v1/pomodoro/sessions", session);
  return response.data;
}

export async function getPomodoroSessions(date?: string): Promise<PomodoroSessionData[]> {
  const params = date ? `?date=${date}` : "";
  const response = await apiClient.get(`/api/v1/pomodoro/sessions${params}`);
  return response.data;
}

export async function getPomodoroAnalytics(): Promise<PomodoroAnalyticsData> {
  const response = await apiClient.get("/api/v1/pomodoro/analytics");
  return response.data;
}
