import apiClient from "@/lib/api-client";

export interface SearchResult {
  type: string;
  id: string;
  title: string;
  subtitle: string | null;
  url: string | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export async function searchAll(query: string, limit: number = 10): Promise<SearchResponse> {
  const response = await apiClient.get("/api/v1/search", { params: { query, limit } });
  return response.data;
}
