import apiClient from "@/lib/api-client";

export interface WorkflowStep {
  id: string;
  tool_name: string;
  parameters: Record<string, unknown>;
  status: string;
  result: unknown;
  error: string | null;
  started_at: number | null;
  completed_at: number | null;
}

export interface Workflow {
  id: string;
  user_id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  status: string;
  created_at: number;
  updated_at: number;
  error: string | null;
  metadata: Record<string, unknown>;
}

export interface WorkflowTemplate {
  name: string;
  name_display: string;
  description: string;
  steps: number;
}

export async function listWorkflows(status?: string): Promise<Workflow[]> {
  const qs = status ? `?status=${status}` : "";
  const { data } = await apiClient.get(`/api/v1/workflows${qs}`);
  return data;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  const { data } = await apiClient.get(`/api/v1/workflows/${id}`);
  return data;
}

export async function createWorkflow(body: {
  name: string;
  steps: Array<{ tool: string; params?: Record<string, unknown> }>;
  description?: string;
}): Promise<Workflow> {
  const { data } = await apiClient.post("/api/v1/workflows", body);
  return data;
}

export async function createFromTemplate(
  templateName: string,
  variables?: Record<string, string>
): Promise<Workflow> {
  const { data } = await apiClient.post(
    `/api/v1/workflows/template/${templateName}`,
    { variables: variables || {} }
  );
  return data;
}

export async function executeWorkflow(
  id: string
): Promise<{ workflow: Workflow; results: unknown[] }> {
  const { data } = await apiClient.post(`/api/v1/workflows/${id}/execute`);
  return data;
}

export async function pauseWorkflow(id: string): Promise<Workflow> {
  const { data } = await apiClient.post(`/api/v1/workflows/${id}/pause`);
  return data;
}

export async function resumeWorkflow(id: string): Promise<Workflow> {
  const { data } = await apiClient.post(`/api/v1/workflows/${id}/resume`);
  return data;
}

export async function cancelWorkflow(id: string): Promise<Workflow> {
  const { data } = await apiClient.post(`/api/v1/workflows/${id}/cancel`);
  return data;
}

export async function listTemplates(): Promise<WorkflowTemplate[]> {
  const { data } = await apiClient.get("/api/v1/workflows/templates");
  return data;
}
