import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;
const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: { get: mockGet, post: mockPost },
}));

describe("ProactiveService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("getNudges fetches nudges", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: "1", title: "Deadline!" }] });
    const { getNudges } = await import("@/lib/proactive-service");
    const result = await getNudges();
    expect(result).toHaveLength(1);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/proactive/nudges");
  });

  it("dismissNudge posts dismiss", async () => {
    mockPost.mockResolvedValueOnce({ data: { dismissed: true } });
    const { dismissNudge } = await import("@/lib/proactive-service");
    const result = await dismissNudge("1");
    expect(result.dismissed).toBe(true);
    expect(mockPost).toHaveBeenCalledWith("/api/v1/proactive/nudges/1/dismiss");
  });

  it("checkDeadlines posts assignments", async () => {
    mockPost.mockResolvedValueOnce({ data: [] });
    const { checkDeadlines } = await import("@/lib/proactive-service");
    await checkDeadlines([{ id: "a1", title: "HW", deadline: "2026-09-15" }]);
    expect(mockPost).toHaveBeenCalledWith("/api/v1/proactive/check-deadlines", {
      assignments: [{ id: "a1", title: "HW", deadline: "2026-09-15" }],
    });
  });
});
