import apiClient from "@/lib/api-client";

export interface DashboardProfile {
  display_name: string;
  avatar_url: string | null;
  xp: number;
  streak: number;
  education_type: string | null;
  education_year: string | null;
}

export interface DashboardSettings {
  daily_goal_hours: number;
  theme: string;
  daily_briefing: boolean;
}

export interface DashboardStats {
  total: number;
  completed: number;
  pending: number;
  in_progress: number;
  overdue: number;
  completion_percentage: number;
  due_today: number;
  due_this_week: number;
  avg_completion_time_hours: number | null;
}

export interface DashboardSubject {
  id: string;
  name: string;
  color: string | null;
  icon: string | null;
}

export interface DashboardEmail {
  unread: number;
  pending_review: number;
}

export interface DashboardData {
  profile: DashboardProfile;
  settings: DashboardSettings;
  stats: DashboardStats;
  recent_assignments: import("@fixly/shared-types").Assignment[];
  subjects: DashboardSubject[];
  email: DashboardEmail;
}

export async function getDashboard(): Promise<DashboardData> {
  const response = await apiClient.get("/api/v1/dashboard");
  return response.data;
}
