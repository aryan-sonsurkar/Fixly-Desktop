import apiClient from "@/lib/api-client";

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  metadata: Record<string, unknown>;
  read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function getNotifications(params: {
  unread_only?: boolean;
  type?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<NotificationListResponse> {
  const response = await apiClient.get("/api/v1/notifications", { params });
  return response.data;
}

export async function getUnreadCount(): Promise<number> {
  const response = await apiClient.get("/api/v1/notifications/unread-count");
  return response.data.unread_count;
}

export async function markNotificationRead(id: string): Promise<NotificationItem> {
  const response = await apiClient.put(`/api/v1/notifications/${id}/read`);
  return response.data;
}

export async function markAllNotificationsRead(): Promise<{ marked_read: number }> {
  const response = await apiClient.put("/api/v1/notifications/read-all");
  return response.data;
}

export async function deleteNotification(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/notifications/${id}`);
}

export async function createNotification(data: {
  type: string;
  title: string;
  message: string;
  metadata?: Record<string, unknown>;
}): Promise<NotificationItem> {
  const response = await apiClient.post("/api/v1/notifications", data);
  return response.data;
}
