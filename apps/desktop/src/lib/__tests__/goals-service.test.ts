import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;
const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();
const mockPut: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: { get: mockGet, post: mockPost, put: mockPut },
}));

describe("GoalsService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("listGoals fetches goals", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: "1", title: "Test" }] });
    const { listGoals } = await import("@/lib/goals-service");
    const result = await listGoals();
    expect(result).toHaveLength(1);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/goals");
  });

  it("listGoals with status filter", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { listGoals } = await import("@/lib/goals-service");
    await listGoals("active");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/goals?status=active");
  });

  it("createGoal posts new goal", async () => {
    const goal = { id: "1", title: "Master Math" };
    mockPost.mockResolvedValueOnce({ data: goal });
    const { createGoal } = await import("@/lib/goals-service");
    const result = await createGoal({ title: "Master Math" });
    expect(result).toEqual(goal);
  });

  it("updateGoalProgress puts progress", async () => {
    const goal = { id: "1", progress: 50 };
    mockPut.mockResolvedValueOnce({ data: goal });
    const { updateGoalProgress } = await import("@/lib/goals-service");
    const result = await updateGoalProgress("1", 50);
    expect(result).toEqual(goal);
    expect(mockPut).toHaveBeenCalledWith("/api/v1/goals/1/progress", { progress: 50 });
  });

  it("listSkills fetches skills", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: "1", name: "Python" }] });
    const { listSkills } = await import("@/lib/goals-service");
    const result = await listSkills();
    expect(result).toHaveLength(1);
  });

  it("createSkill posts new skill", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "1", name: "Python" } });
    const { createSkill } = await import("@/lib/goals-service");
    const result = await createSkill({ name: "Python" });
    expect(result.name).toBe("Python");
  });

  it("listRoadmaps fetches roadmaps", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { listRoadmaps } = await import("@/lib/goals-service");
    await listRoadmaps();
    expect(mockGet).toHaveBeenCalledWith("/api/v1/roadmaps");
  });

  it("createRoadmap posts new roadmap", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "1", title: "ML Roadmap" } });
    const { createRoadmap } = await import("@/lib/goals-service");
    const result = await createRoadmap({
      title: "ML Roadmap",
      steps: [{ title: "Learn Python" }],
    });
    expect(result.title).toBe("ML Roadmap");
  });
});
