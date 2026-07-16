import apiClient from "@/lib/api-client";
import type { Assignment } from "@fixly/shared-types";

export interface AssignmentsQuery {
  search?: string;
  status?: string;
  priority?: string;
  subject_id?: string;
  tags?: string[];
  is_archived?: boolean;
  is_favorite?: boolean;
  is_pinned?: boolean;
  due_date_from?: string;
  due_date_to?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse {
  data: Assignment[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AssignmentStats {
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

export async function getAssignments(query: AssignmentsQuery = {}): Promise<PaginatedResponse> {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        value.forEach((v) => params.append(key, v));
      } else {
        params.set(key, String(value));
      }
    }
  });
  const response = await apiClient.get(`/api/v1/assignments?${params.toString()}`);
  return response.data;
}

export async function getAssignment(id: string): Promise<Assignment> {
  const response = await apiClient.get(`/api/v1/assignments/${id}`);
  return response.data;
}

export interface CreateAssignmentPayload {
  title: string;
  description?: string | null;
  subject_id?: string | null;
  priority?: string;
  status?: string;
  due_date?: string | null;
  estimated_study_time?: number | null;
  tags?: string[];
  notes?: string | null;
  is_pinned?: boolean;
  is_favorite?: boolean;
}

export interface UpdateAssignmentPayload {
  title?: string;
  description?: string | null;
  subject_id?: string | null;
  priority?: string;
  status?: string;
  due_date?: string | null;
  estimated_study_time?: number | null;
  tags?: string[];
  notes?: string | null;
  is_archived?: boolean;
  is_pinned?: boolean;
  is_favorite?: boolean;
}

export async function createAssignment(data: CreateAssignmentPayload): Promise<Assignment> {
  const response = await apiClient.post("/api/v1/assignments", data);
  return response.data;
}

export async function updateAssignment(id: string, data: UpdateAssignmentPayload): Promise<Assignment> {
  const response = await apiClient.put(`/api/v1/assignments/${id}`, data);
  return response.data;
}

export async function deleteAssignment(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/assignments/${id}`);
}

export async function duplicateAssignment(id: string): Promise<Assignment> {
  const response = await apiClient.post(`/api/v1/assignments/${id}/duplicate`);
  return response.data;
}

export async function bulkAction(
  ids: string[],
  action: string,
  value?: string | boolean | null,
): Promise<{ affected: number; data: Assignment[] }> {
  const response = await apiClient.post("/api/v1/assignments/bulk", { ids, action, value });
  return response.data;
}

export async function getAssignmentStats(): Promise<AssignmentStats> {
  const response = await apiClient.get("/api/v1/assignments/stats");
  return response.data;
}

export async function getAssignmentAttachments(assignmentId: string): Promise<Attachment[]> {
  const response = await apiClient.get(`/api/v1/assignments/${assignmentId}/attachments`);
  return response.data;
}

export async function uploadAttachment(assignmentId: string, file: File): Promise<Attachment> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("assignment_id", assignmentId);
  const response = await apiClient.post("/api/v1/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  await apiClient.delete(`/api/v1/upload/${attachmentId}`);
}

interface Attachment {
  id: string;
  assignment_id: string;
  user_id: string;
  file_name: string;
  file_type: string | null;
  file_size: number | null;
  storage_path: string;
  created_at: string;
}
