import apiClient from "@/lib/api-client";

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description: string;
  category: string;
  target_date: string | null;
  status: string;
  progress: number;
  milestones: Array<{ title: string; completed: boolean }>;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  user_id: string;
  name: string;
  category: string;
  level: string;
  evidence: string[];
  last_practiced_at: string | null;
  created_at: string;
}

export interface Roadmap {
  id: string;
  user_id: string;
  title: string;
  goal_id: string | null;
  steps: Array<{
    id: string;
    title: string;
    description: string;
    status: string;
    resources: string[];
    estimated_hours: number;
    order: number;
  }>;
  created_at: string;
  updated_at: string;
}

// Goals
export async function listGoals(status?: string): Promise<Goal[]> {
  const qs = status ? `?status=${status}` : "";
  const { data } = await apiClient.get(`/api/v1/goals${qs}`);
  return data;
}

export async function createGoal(body: {
  title: string;
  description?: string;
  category?: string;
  target_date?: string;
}): Promise<Goal> {
  const { data } = await apiClient.post("/api/v1/goals", body);
  return data;
}

export async function updateGoalProgress(
  id: string,
  progress: number
): Promise<Goal> {
  const { data } = await apiClient.put(`/api/v1/goals/${id}/progress`, {
    progress,
  });
  return data;
}

// Skills
export async function listSkills(category?: string): Promise<Skill[]> {
  const qs = category ? `?category=${category}` : "";
  const { data } = await apiClient.get(`/api/v1/skills${qs}`);
  return data;
}

export async function createSkill(body: {
  name: string;
  category?: string;
  level?: string;
}): Promise<Skill> {
  const { data } = await apiClient.post("/api/v1/skills", body);
  return data;
}

// Roadmaps
export async function listRoadmaps(): Promise<Roadmap[]> {
  const { data } = await apiClient.get("/api/v1/roadmaps");
  return data;
}

export async function createRoadmap(body: {
  title: string;
  steps: Array<{ title: string; description?: string; estimated_hours?: number }>;
  goal_id?: string;
}): Promise<Roadmap> {
  const { data } = await apiClient.post("/api/v1/roadmaps", body);
  return data;
}
