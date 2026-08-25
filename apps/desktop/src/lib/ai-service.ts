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
  provider_model?: string | null;
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

export interface ProviderDetail {
  name: string;
  available: boolean;
  installed: boolean;
  running: boolean;
  model_count: number;
  models: string[];
  error: string | null;
  selected_model?: string | null;
}

export interface ProviderDetailResponse {
  providers: Record<string, ProviderDetail>;
}

export interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
}

export async function sendChat(data: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post("/api/v1/ai/chat", data);
  return response.data;
}

export async function sendChatStream(
  data: ChatRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const { getAccessToken } = await import("@/lib/secure-storage");
  const { ensureBackendPort } = await import("@/lib/api-client");
  await ensureBackendPort();
  // Resolve base URL same as api-client (dynamic Tauri port)
  const base = (apiClient.defaults.baseURL as string) || "http://127.0.0.1:8000";
  const token = await getAccessToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${base}/api/v1/ai/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ ...data, stream: true }),
    signal,
  });
  if (!resp.ok || !resp.body) {
    throw new Error(
      resp.status === 503
        ? "Fixly AI is currently unavailable. Please retry."
        : `Unable to start the AI response (HTTP ${resp.status}).`,
    );
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completeResponse: ChatResponse | null = null;
  // Stream tokens incrementally
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const jsonStr = trimmed.slice(5).trim();
      let event: { token?: unknown; error?: unknown; done?: unknown; message?: Message; conversation?: Conversation };
      try {
        event = JSON.parse(jsonStr) as typeof event;
      } catch {
        continue;
      }
      if (typeof event.error === "string") throw new Error(event.error);
      if (typeof event.token === "string") onToken(event.token);
      if (event.done && event.message && event.conversation) {
        completeResponse = { message: event.message, conversation: event.conversation };
      }
    }
  }
  if (!completeResponse) throw new Error("The AI response ended before it was saved. Please retry.");
  return completeResponse;
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

export async function checkProviderDetail(): Promise<ProviderDetailResponse> {
  const response = await apiClient.get("/api/v1/ai/providers/detail");
  return response.data;
}

export async function listOllamaModels(forceRefresh = false): Promise<OllamaModel[]> {
  const response = await apiClient.get("/api/v1/ai/providers/ollama/models", {
    params: forceRefresh ? { refresh: true } : undefined,
  });
  return response.data;
}
