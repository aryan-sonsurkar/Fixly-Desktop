import apiClient from "@/lib/api-client";
import { useAnalyticsStore } from "@/stores/analytics-store";

export interface FeedbackPayload {
  type: "bug" | "feature" | "rating";
  title?: string;
  description: string;
  rating?: number;
  attach_logs: boolean;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
  const logs = payload.attach_logs
    ? useAnalyticsStore.getState().flush().slice(-50)
    : [];

  await apiClient.post("/api/v1/feedback", {
    ...payload,
    logs: logs.length > 0 ? JSON.stringify(logs) : undefined,
    user_agent: navigator.userAgent,
    url: window.location.hash,
  });
}
