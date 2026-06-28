export type Status = "pending" | "in_progress" | "completed" | "cancelled";

export type Priority = "low" | "medium" | "high" | "urgent";

export type Theme = "dark" | "light" | "system";

export type NotificationType =
  | "assignment_reminder"
  | "due_date"
  | "daily_briefing"
  | "pomodoro"
  | "email"
  | "system";

export type AiContextType = "chat" | "code" | "study" | "pdf" | "image";

export type AiRole = "user" | "assistant";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  xp: number;
  streak: number;
  created_at: string;
  updated_at: string;
}

export interface Assignment {
  id: string;
  user_id: string;
  subject_id: string | null;
  title: string;
  description: string | null;
  status: "pending" | "in_progress" | "completed" | "cancelled" | "overdue";
  priority: Priority;
  due_date: string | null;
  estimated_study_time: number | null;
  tags: string[] | null;
  notes: string | null;
  completion_date: string | null;
  is_archived: boolean;
  is_pinned: boolean;
  is_favorite: boolean;
  source: "manual" | "email" | "ai";
  ai_draft: string | null;
  ai_draft_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  assignment_id: string;
  user_id: string;
  file_name: string;
  file_type: string | null;
  file_size: number | null;
  storage_path: string;
  created_at: string;
}

export interface Subject {
  id: string;
  user_id: string;
  name: string;
  color: string | null;
  icon: string | null;
  credits: number | null;
  created_at: string;
}

export interface Profile {
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
  created_at: string;
  updated_at: string;
}

export interface Settings {
  id: string;
  theme: "dark" | "light" | "system";
  daily_goal_hours: number;
  pomodoro_focus: number;
  pomodoro_break: number;
  notification_enabled: boolean;
  assignment_reminders: boolean;
  daily_briefing: boolean;
  email_monitoring: boolean;
  email_sync_enabled: boolean;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string | null;
  type: NotificationType;
  read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface StudySession {
  id: string;
  user_id: string;
  subject_id: string | null;
  duration_minutes: number;
  started_at: string;
  ended_at: string | null;
  created_at: string;
}

export interface PomodoroSession {
  id: string;
  user_id: string;
  focus_duration: number;
  break_duration: number;
  cycles_completed: number;
  total_focus_minutes: number;
  date: string;
  created_at: string;
}

export interface AiMessage {
  id: string;
  user_id: string;
  role: AiRole;
  content: string;
  model: string | null;
  tokens_used: number | null;
  context_type: AiContextType | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  error: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
