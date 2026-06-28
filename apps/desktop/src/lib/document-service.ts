import apiClient from "@/lib/api-client";

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  page_count: number;
  status: "pending" | "processing" | "processed" | "failed";
  error_message: string | null;
  processing_time_ms: number | null;
  storage_path: string | null;
  subject_id: string | null;
  is_favorite: boolean;
  last_opened_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  chunk_type: string;
  content: string;
  heading: string | null;
  page_number: number | null;
  token_count: number;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
  conversation_ids: string[];
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentChatRequest {
  document_id: string;
  message: string;
  conversation_id?: string;
}

export interface DocumentChatResponse {
  message: {
    id: string;
    content: string;
    role: string;
    created_at: string;
  };
  conversation: {
    id: string;
    title: string;
  };
  chunks_used: DocumentChunk[];
}

export interface GenerateContentResponse {
  message: {
    id: string;
    content: string;
    role: string;
    created_at: string;
  };
  conversation: {
    id: string;
    title: string;
  };
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/api/v1/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function processDocument(id: string): Promise<Record<string, unknown>> {
  const response = await apiClient.post(`/api/v1/documents/${id}/process`);
  return response.data;
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  const response = await apiClient.get(`/api/v1/documents/${id}`);
  return response.data;
}

export async function updateDocument(id: string, data: Partial<Document>): Promise<Document> {
  const response = await apiClient.put(`/api/v1/documents/${id}`, data);
  return response.data;
}

export async function renameDocument(id: string, original_name: string): Promise<Document> {
  const response = await apiClient.put(`/api/v1/documents/${id}/rename`, { original_name });
  return response.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/documents/${id}`);
}

export async function listDocuments(params: {
  page?: number;
  page_size?: number;
  subject_id?: string;
  status?: string;
  file_type?: string;
  search?: string;
  favorites_only?: boolean;
} = {}): Promise<DocumentListResponse> {
  const response = await apiClient.get("/api/v1/documents", { params });
  return response.data;
}

export async function getRecentDocuments(limit = 5): Promise<Document[]> {
  const response = await apiClient.get("/api/v1/documents/recent", { params: { limit } });
  return response.data;
}

export async function chatWithDocument(data: DocumentChatRequest): Promise<DocumentChatResponse> {
  const response = await apiClient.post("/api/v1/documents/chat", data);
  return response.data;
}

export async function summarizeDocument(id: string, maxLength = 500): Promise<GenerateContentResponse> {
  const response = await apiClient.post(`/api/v1/documents/${id}/summarize`, { max_length: maxLength });
  return response.data;
}

export async function generateNotes(id: string, style = "detailed"): Promise<GenerateContentResponse> {
  const response = await apiClient.post(`/api/v1/documents/${id}/notes`, { style });
  return response.data;
}

export async function generateFlashcards(id: string, count = 10): Promise<GenerateContentResponse> {
  const response = await apiClient.post(`/api/v1/documents/${id}/flashcards`, { count });
  return response.data;
}

export async function generateQuiz(id: string, count = 5, difficulty = "medium"): Promise<GenerateContentResponse> {
  const response = await apiClient.post(`/api/v1/documents/${id}/quiz`, { count, difficulty });
  return response.data;
}
