import apiClient from "@/lib/api-client";

export interface Opportunity {
  id: string;
  user_id: string;
  title: string;
  company: string;
  category: string;
  url: string | null;
  description: string;
  deadline: string | null;
  status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export async function listOpportunities(status?: string): Promise<Opportunity[]> {
  const qs = status ? `?status=${status}` : "";
  const { data } = await apiClient.get(`/api/v1/opportunities${qs}`);
  return data;
}

export async function saveOpportunity(body: {
  title: string;
  company: string;
  category?: string;
  url?: string;
  description?: string;
  deadline?: string;
}): Promise<Opportunity> {
  const { data } = await apiClient.post("/api/v1/opportunities", body);
  return data;
}

export async function updateOpportunityStatus(
  id: string,
  status: string
): Promise<Opportunity> {
  const { data } = await apiClient.put(`/api/v1/opportunities/${id}/status`, {
    status,
  });
  return data;
}

export async function deleteOpportunity(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/opportunities/${id}`);
}
