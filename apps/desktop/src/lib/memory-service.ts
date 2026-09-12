import apiClient from "@/lib/api-client";

export interface Memory {
  id: string;
  user_id: string;
  category: string;
  content: string;
  confidence: number;
  source: string;
  source_document_id?: string | null;
  source_conversation_id?: string | null;
  created_at: string;
  updated_at: string;
  last_reinforced_at?: string | null;
  is_archived: boolean;
}

export interface MemoryStats {
  total_memories: number;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
  avg_confidence: number;
}

export async function listMemories(params?: {
  category?: string;
  archived?: boolean;
  limit?: number;
}): Promise<Memory[]> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.archived !== undefined) query.set("archived", String(params.archived));
  if (params?.limit) query.set("limit", String(params.limit));
  const qs = query.toString();
  const { data } = await apiClient.get(`/api/v1/memory${qs ? `?${qs}` : ""}`);
  return data;
}

export async function getMemory(id: string): Promise<Memory> {
  const { data } = await apiClient.get(`/api/v1/memory/${id}`);
  return data;
}

export async function createMemory(body: {
  content: string;
  category: string;
  source?: string;
  confidence?: number;
}): Promise<Memory> {
  const { data } = await apiClient.post("/api/v1/memory", body);
  return data;
}

export async function updateMemory(
  id: string,
  body: { content?: string; category?: string }
): Promise<Memory> {
  const { data } = await apiClient.put(`/api/v1/memory/${id}`, body);
  return data;
}

export async function deleteMemory(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/memory/${id}`);
}

export async function archiveMemory(id: string): Promise<Memory> {
  const { data } = await apiClient.post(`/api/v1/memory/${id}/archive`);
  return data;
}

export async function unarchiveMemory(id: string): Promise<Memory> {
  const { data } = await apiClient.post(`/api/v1/memory/${id}/unarchive`);
  return data;
}

export async function searchMemories(body: {
  query: string;
  top_k?: number;
  min_confidence?: number;
}): Promise<Memory[]> {
  const { data } = await apiClient.post("/api/v1/memory/search", body);
  return data;
}

export async function getMemoryStats(): Promise<MemoryStats> {
  const { data } = await apiClient.get("/api/v1/memory/stats");
  return data;
}

export async function resetAllMemories(): Promise<{ deleted: number }> {
  const { data } = await apiClient.post("/api/v1/memory/reset", {
    confirmation: "RESET",
  });
  return data;
}
