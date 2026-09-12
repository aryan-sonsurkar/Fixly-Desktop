import apiClient from "@/lib/api-client";

export interface Nudge {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  priority: string;
  action_suggestion: string | null;
  created_at: string;
  dismissed: boolean;
}

export async function getNudges(): Promise<Nudge[]> {
  const { data } = await apiClient.get("/api/v1/proactive/nudges");
  return data;
}

export async function dismissNudge(id: string): Promise<{ dismissed: boolean }> {
  const { data } = await apiClient.post(`/api/v1/proactive/nudges/${id}/dismiss`);
  return data;
}

export async function checkDeadlines(
  assignments: Array<{ id: string; title: string; deadline: string }>
): Promise<Nudge[]> {
  const { data } = await apiClient.post("/api/v1/proactive/check-deadlines", {
    assignments,
  });
  return data;
}
