import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;
const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: { get: mockGet, post: mockPost },
}));

describe("AcademicService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("getAcademicProfile fetches profile", async () => {
    mockGet.mockResolvedValueOnce({ data: { user_id: "u1", subjects: {} } });
    const { getAcademicProfile } = await import("@/lib/academic-service");
    const result = await getAcademicProfile();
    expect(result.user_id).toBe("u1");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/academic/profile");
  });

  it("updateScore posts score", async () => {
    mockPost.mockResolvedValueOnce({ data: { subjects: { Math: { average_score: 85 } } } });
    const { updateScore } = await import("@/lib/academic-service");
    await updateScore({ subject: "Math", score: 85 });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/academic/scores", { subject: "Math", score: 85 });
  });

  it("getWeakSubjects fetches weak subjects", async () => {
    mockGet.mockResolvedValueOnce({ data: { weak_subjects: ["Physics"] } });
    const { getWeakSubjects } = await import("@/lib/academic-service");
    const result = await getWeakSubjects();
    expect(result.weak_subjects).toContain("Physics");
  });

  it("getWeakSubjects with threshold", async () => {
    mockGet.mockResolvedValueOnce({ data: { weak_subjects: [] } });
    const { getWeakSubjects } = await import("@/lib/academic-service");
    await getWeakSubjects(70);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/academic/weak-subjects?threshold=70");
  });

  it("getRecommendations fetches recommendations", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ subject: "Math", reason: "Low scores" }] });
    const { getRecommendations } = await import("@/lib/academic-service");
    const result = await getRecommendations();
    expect(result).toHaveLength(1);
  });

  it("detectWeaknesses fetches weaknesses", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ subject: "Math", topic: "Calculus" }] });
    const { detectWeaknesses } = await import("@/lib/academic-service");
    const result = await detectWeaknesses();
    expect(result).toHaveLength(1);
  });

  it("getSubjectHealth fetches health", async () => {
    mockGet.mockResolvedValueOnce({ data: { Math: { score: 85, average: 80 } } });
    const { getSubjectHealth } = await import("@/lib/academic-service");
    const result = await getSubjectHealth();
    expect(result.Math.score).toBe(85);
  });
});
