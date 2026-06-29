import apiClient from "@/lib/api-client";

export interface DailyMissionResponse {
  content: string;
  generated_at: string;
  context_summary: Record<string, unknown>;
}

export interface ProductivityCoachResponse {
  content: string;
  generated_at: string;
}

export interface RescheduleResponse {
  content: string;
  generated_at: string;
}

export interface RiskAssessmentResponse {
  content: string;
  generated_at: string;
  risk_level: string;
  academic_health_score: number;
}

export interface WeeklyReviewResponse {
  content: string;
  generated_at: string;
}

export interface InsightsResponse {
  content: string;
  generated_at: string;
}

export interface SmartCommandResponse {
  content: string;
  command_type: string;
  confidence: number;
  generated_at: string;
}

export interface CopilotChatResponse {
  content: string;
  conversation_id: string;
  generated_at: string;
}

export async function getDailyMission(): Promise<DailyMissionResponse> {
  const response = await apiClient.get("/api/v1/copilot/mission");
  return response.data;
}

export async function getProductivityCoach(): Promise<ProductivityCoachResponse> {
  const response = await apiClient.get("/api/v1/copilot/coach");
  return response.data;
}

export async function reschedule(message: string): Promise<RescheduleResponse> {
  const response = await apiClient.post("/api/v1/copilot/reschedule", { message });
  return response.data;
}

export async function assessRisk(): Promise<RiskAssessmentResponse> {
  const response = await apiClient.get("/api/v1/copilot/risk");
  return response.data;
}

export async function getWeeklyReview(): Promise<WeeklyReviewResponse> {
  const response = await apiClient.get("/api/v1/copilot/review");
  return response.data;
}

export async function getInsights(): Promise<InsightsResponse> {
  const response = await apiClient.get("/api/v1/copilot/insights");
  return response.data;
}

export async function interpretCommand(command: string): Promise<SmartCommandResponse> {
  const response = await apiClient.post("/api/v1/copilot/command", { command });
  return response.data;
}

export async function copilotChat(message: string, conversationId?: string): Promise<CopilotChatResponse> {
  const response = await apiClient.post("/api/v1/copilot/chat", { message, conversation_id: conversationId });
  return response.data;
}
