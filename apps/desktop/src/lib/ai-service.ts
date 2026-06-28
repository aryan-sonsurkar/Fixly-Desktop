import apiClient from "@/lib/api-client";

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: Message[];
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  provider?: string | null;
  tokens?: number | null;
  feedback?: string | null;
  created_at: string;
}

export interface ChatRequest {
  conversation_id?: string;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  message: Message;
  conversation: Conversation;
}

export interface AISettings {
  preferred_provider: string;
  temperature: number;
  max_tokens: number;
  streaming_enabled: boolean;
  system_prompt: string | null;
  academic_context?: boolean;
  conversation_memory?: number;
  fallback_provider?: string;
  ai_enabled?: boolean;
  ollama_available: boolean;
  gemini_available: boolean;
}

export async function sendChat(data: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post("/api/v1/ai/chat", data);
  return response.data;
}

export async function regenerateMessage(conversation_id: string, message_id: string): Promise<ChatResponse> {
  const response = await apiClient.post("/api/v1/ai/regenerate", { conversation_id, message_id });
  return response.data;
}

export async function getConversations(): Promise<Conversation[]> {
  const response = await apiClient.get("/api/v1/ai/conversations");
  return response.data;
}

export async function searchConversations(query: string): Promise<Conversation[]> {
  const response = await apiClient.get("/api/v1/ai/conversations/search", { params: { query } });
  return response.data;
}

export async function createConversation(title?: string): Promise<Conversation> {
  const response = await apiClient.post("/api/v1/ai/conversations", { title });
  return response.data;
}

export async function getConversation(id: string): Promise<Conversation> {
  const response = await apiClient.get(`/api/v1/ai/conversations/${id}`);
  return response.data;
}

export async function updateConversation(id: string, data: Partial<Conversation>): Promise<Conversation> {
  const response = await apiClient.put(`/api/v1/ai/conversations/${id}`, data);
  return response.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/ai/conversations/${id}`);
}

export async function setMessageFeedback(messageId: string, feedback: string | null): Promise<Message> {
  const response = await apiClient.put(`/api/v1/ai/messages/${messageId}/feedback`, { feedback });
  return response.data;
}

export async function editMessage(messageId: string, content: string): Promise<Message> {
  const response = await apiClient.put(`/api/v1/ai/messages/${messageId}`, { content });
  return response.data;
}

export async function deleteMessage(messageId: string): Promise<void> {
  await apiClient.delete(`/api/v1/ai/messages/${messageId}`);
}

export async function getAISettings(): Promise<AISettings> {
  const response = await apiClient.get("/api/v1/ai/settings");
  return response.data;
}

export async function updateAISettings(data: Partial<AISettings>): Promise<AISettings> {
  const response = await apiClient.put("/api/v1/ai/settings", data);
  return response.data;
}

export async function checkAIProviders(): Promise<Record<string, boolean>> {
  const response = await apiClient.get("/api/v1/ai/providers");
  return response.data;
}
