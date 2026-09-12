import apiClient from "@/lib/api-client";

export interface AcademicProfile {
  user_id: string;
  subjects: Record<
    string,
    {
      subject: string;
      scores: number[];
      average_score: number;
      trend: string;
      total_study_hours: number;
      weak_topics: string[];
      strong_topics: string[];
    }
  >;
  strengths: string[];
  weaknesses: string[];
  goals: string[];
  study_patterns: Record<string, unknown>;
  updated_at: string;
}

export interface WeaknessSignal {
  subject: string;
  topic: string;
  type: string;
  severity: string;
  evidence: string;
  recommendation: string;
}

export interface SubjectHealth {
  score: number;
  average: number;
  trend: string;
  study_hours: number;
  weak_topics: string[];
  strong_topics: string[];
}

export async function getAcademicProfile(): Promise<AcademicProfile> {
  const { data } = await apiClient.get("/api/v1/academic/profile");
  return data;
}

export async function updateScore(body: {
  subject: string;
  score: number;
}): Promise<AcademicProfile> {
  const { data } = await apiClient.post("/api/v1/academic/scores", body);
  return data;
}

export async function getWeakSubjects(
  threshold?: number
): Promise<{ weak_subjects: string[] }> {
  const qs = threshold ? `?threshold=${threshold}` : "";
  const { data } = await apiClient.get(`/api/v1/academic/weak-subjects${qs}`);
  return data;
}

export async function getRecommendations(): Promise<
  Array<{
    subject: string;
    reason: string;
    priority: string;
    suggested_action: string;
  }>
> {
  const { data } = await apiClient.get("/api/v1/academic/recommendations");
  return data;
}

export async function detectWeaknesses(): Promise<WeaknessSignal[]> {
  const { data } = await apiClient.get("/api/v1/academic/weaknesses");
  return data;
}

export async function getSubjectHealth(): Promise<
  Record<string, SubjectHealth>
> {
  const { data } = await apiClient.get("/api/v1/academic/health");
  return data;
}
