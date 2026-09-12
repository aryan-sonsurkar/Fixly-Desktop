import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;
const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: { get: mockGet, post: mockPost },
}));

describe("WorkflowService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("listWorkflows fetches workflows", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: "w1", name: "Test" }] });
    const { listWorkflows } = await import("@/lib/workflow-service");
    const result = await listWorkflows();
    expect(result).toHaveLength(1);
  });

  it("listWorkflows with status filter", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { listWorkflows } = await import("@/lib/workflow-service");
    await listWorkflows("running");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/workflows?status=running");
  });

  it("getWorkflow fetches single workflow", async () => {
    mockGet.mockResolvedValueOnce({ data: { id: "w1", name: "Test" } });
    const { getWorkflow } = await import("@/lib/workflow-service");
    await getWorkflow("w1");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/workflows/w1");
  });

  it("createWorkflow posts new workflow", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "w1", name: "Custom" } });
    const { createWorkflow } = await import("@/lib/workflow-service");
    const result = await createWorkflow({
      name: "Custom",
      steps: [{ tool: "search" }],
    });
    expect(result.name).toBe("Custom");
  });

  it("createFromTemplate posts template", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "w1", name: "Study Plan" } });
    const { createFromTemplate } = await import("@/lib/workflow-service");
    await createFromTemplate("study_plan", { subject: "Math" });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/workflows/template/study_plan", {
      variables: { subject: "Math" },
    });
  });

  it("executeWorkflow posts execute", async () => {
    mockPost.mockResolvedValueOnce({ data: { workflow: {}, results: [] } });
    const { executeWorkflow } = await import("@/lib/workflow-service");
    await executeWorkflow("w1");
    expect(mockPost).toHaveBeenCalledWith("/api/v1/workflows/w1/execute");
  });

  it("pauseWorkflow posts pause", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "w1", status: "paused" } });
    const { pauseWorkflow } = await import("@/lib/workflow-service");
    await pauseWorkflow("w1");
    expect(mockPost).toHaveBeenCalledWith("/api/v1/workflows/w1/pause");
  });

  it("resumeWorkflow posts resume", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "w1", status: "running" } });
    const { resumeWorkflow } = await import("@/lib/workflow-service");
    await resumeWorkflow("w1");
    expect(mockPost).toHaveBeenCalledWith("/api/v1/workflows/w1/resume");
  });

  it("cancelWorkflow posts cancel", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "w1", status: "cancelled" } });
    const { cancelWorkflow } = await import("@/lib/workflow-service");
    await cancelWorkflow("w1");
    expect(mockPost).toHaveBeenCalledWith("/api/v1/workflows/w1/cancel");
  });

  it("listTemplates fetches templates", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ name: "study_plan", name_display: "Study Plan" }] });
    const { listTemplates } = await import("@/lib/workflow-service");
    const result = await listTemplates();
    expect(result).toHaveLength(1);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/workflows/templates");
  });
});
