import apiClient from "@/lib/api-client";

export interface PlanResponse {
  plan_type: string;
  content: string;
  conversation_id: string;
  generated_at: string;
  context_summary?: Record<string, unknown>;
}

export async function generateDailyPlan(): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/daily");
  return response.data;
}

export async function generateWeeklyPlan(): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/weekly");
  return response.data;
}

export async function generateRevisionPlan(subject_ids?: string[]): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/revision", { subject_ids });
  return response.data;
}
