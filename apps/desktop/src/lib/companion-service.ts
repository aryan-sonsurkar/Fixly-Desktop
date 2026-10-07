import apiClient from "@/lib/api-client";
import type { ChatResponse, Message, Conversation } from "@/lib/ai-service";

export interface CompanionAction {
  kind: "assignment" | "topic" | "start";
  key: string;
  title: string;
  subject: string;
  due_date: string | null;
  overdue: boolean;
  priority: string;
  suggested_minutes: number;
  reason: string;
  document_id: string | null;
  document_name: string | null;
}

export interface NextActionResponse {
  action: CompanionAction | null;
  alternates: CompanionAction[];
  empty_reason: string | null;
}

export interface ContinueSessionResponse extends NextActionResponse {
  resumed: boolean;
}

export async function getNextAction(options?: {
  available_minutes?: number;
  exclude_keys?: string[];
}): Promise<NextActionResponse> {
  const response = await apiClient.post("/api/v1/companion/next-action", {
    available_minutes: options?.available_minutes ?? null,
    exclude_keys: options?.exclude_keys ?? [],
  });
  return response.data;
}

export async function continueCompanionSession(options?: {
  current_key?: string | null;
  available_minutes?: number;
}): Promise<ContinueSessionResponse> {
  const response = await apiClient.post("/api/v1/companion/continue", {
    current_key: options?.current_key ?? null,
    available_minutes: options?.available_minutes ?? null,
  });
  return response.data;
}

export async function sendCompanionChat(data: {
  message: string;
  conversation_id?: string;
}): Promise<ChatResponse> {
  const response = await apiClient.post("/api/v1/companion/chat", data, {
    timeout: 300000,
  });
  return response.data;
}

export async function sendCompanionChatStream(
  data: { message: string; conversation_id?: string },
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const { getAccessToken } = await import("@/lib/secure-storage");
  const { ensureBackendPort } = await import("@/lib/api-client");
  await ensureBackendPort();
  const base = (apiClient.defaults.baseURL as string) || "http://127.0.0.1:8000";
  const token = await getAccessToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${base}/api/v1/companion/chat/stream`, {
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
