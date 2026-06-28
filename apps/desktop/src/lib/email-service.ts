import apiClient from "@/lib/api-client";

export interface EmailAccount {
  id: string;
  user_id: string;
  email: string;
  provider: string;
  sync_enabled: boolean;
  sync_status: string;
  sync_error: string | null;
  total_emails: number;
  last_synced_at: string | null;
  daily_briefing_enabled: boolean;
  briefing_time: string;
  auto_create_assignments: boolean;
  confidence_threshold: number;
  attachment_download: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailMessage {
  id: string;
  user_id: string;
  account_id: string;
  message_id: string;
  thread_id: string | null;
  subject: string;
  from_name: string | null;
  from_email: string;
  to_emails: string[];
  body_text: string | null;
  received_at: string;
  is_read: boolean;
  is_starred: boolean;
  has_attachments: boolean;
  labels: string[];
  classification: { category: string; confidence: number } | null;
  assignment: Record<string, unknown> | null;
  created_at: string;
}

export interface EmailAssignment {
  id: string;
  email_id: string;
  subject: string | null;
  title: string | null;
  due_date: string | null;
  priority: string;
  teacher_name: string | null;
  description: string | null;
  course: string | null;
  confidence: number;
  status: string;
  assignment_id: string | null;
  email: EmailMessage | null;
  created_at: string;
}

export interface EmailListResponse {
  messages: EmailMessage[];
  total: number;
  page: number;
  page_size: number;
}

export interface EmailBriefingResponse {
  content: string;
  conversation_id: string;
  generated_at: string;
}

export interface EmailDashboardStats {
  accounts_connected: number;
  unread_academic: number;
  pending_review: number;
  recent_emails: EmailMessage[];
  last_sync: string | null;
}

export async function connectEmailAccount(data: {
  email: string;
  provider: string;
  access_token: string;
  refresh_token?: string;
}): Promise<EmailAccount> {
  const response = await apiClient.post("/api/v1/email/accounts/connect", data);
  return response.data;
}

export async function getEmailAccounts(): Promise<EmailAccount[]> {
  const response = await apiClient.get("/api/v1/email/accounts");
  return response.data;
}

export async function updateEmailAccount(id: string, data: Partial<EmailAccount>): Promise<EmailAccount> {
  const response = await apiClient.put(`/api/v1/email/accounts/${id}`, data);
  return response.data;
}

export async function deleteEmailAccount(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/email/accounts/${id}`);
}

export async function syncEmailAccount(accountId: string): Promise<{ synced: number; duration_ms: number }> {
  const response = await apiClient.post(`/api/v1/email/accounts/${accountId}/sync`);
  return response.data;
}

export async function getEmailMessages(params: {
  account_id?: string;
  page?: number;
  page_size?: number;
  unread_only?: boolean;
  search?: string;
} = {}): Promise<EmailListResponse> {
  const response = await apiClient.get("/api/v1/email/messages", { params });
  return response.data;
}

export async function getEmailMessage(id: string): Promise<EmailMessage> {
  const response = await apiClient.get(`/api/v1/email/messages/${id}`);
  return response.data;
}

export async function markEmailRead(id: string): Promise<EmailMessage> {
  const response = await apiClient.put(`/api/v1/email/messages/${id}/read`);
  return response.data;
}

export async function getReviewQueue(): Promise<EmailAssignment[]> {
  const response = await apiClient.get("/api/v1/email/review-queue");
  return response.data;
}

export async function reviewAssignment(
  id: string, status: string, edits?: Record<string, unknown>,
): Promise<EmailAssignment> {
  const response = await apiClient.put(`/api/v1/email/review-queue/${id}`, { status, edits });
  return response.data;
}

export async function generateBriefing(): Promise<EmailBriefingResponse> {
  const response = await apiClient.post("/api/v1/email/briefing");
  return response.data;
}

export async function getEmailDashboard(): Promise<EmailDashboardStats> {
  const response = await apiClient.get("/api/v1/email/dashboard");
  return response.data;
}
