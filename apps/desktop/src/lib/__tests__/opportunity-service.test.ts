import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;
const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();
const mockPut: MockFn = vi.fn();
const mockDelete: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: { get: mockGet, post: mockPost, put: mockPut, delete: mockDelete },
}));

describe("OpportunityService", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("listOpportunities fetches all", async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: "1", title: "Internship" }] });
    const { listOpportunities } = await import("@/lib/opportunity-service");
    const result = await listOpportunities();
    expect(result).toHaveLength(1);
  });

  it("listOpportunities with status filter", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });
    const { listOpportunities } = await import("@/lib/opportunity-service");
    await listOpportunities("applied");
    expect(mockGet).toHaveBeenCalledWith("/api/v1/opportunities?status=applied");
  });

  it("saveOpportunity posts new", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "1", title: "SWE Intern" } });
    const { saveOpportunity } = await import("@/lib/opportunity-service");
    const result = await saveOpportunity({ title: "SWE Intern", company: "Google" });
    expect(result.title).toBe("SWE Intern");
  });

  it("updateOpportunityStatus puts status", async () => {
    mockPut.mockResolvedValueOnce({ data: { id: "1", status: "applied" } });
    const { updateOpportunityStatus } = await import("@/lib/opportunity-service");
    await updateOpportunityStatus("1", "applied");
    expect(mockPut).toHaveBeenCalledWith("/api/v1/opportunities/1/status", { status: "applied" });
  });

  it("deleteOpportunity calls delete", async () => {
    mockDelete.mockResolvedValueOnce({});
    const { deleteOpportunity } = await import("@/lib/opportunity-service");
    await deleteOpportunity("1");
    expect(mockDelete).toHaveBeenCalledWith("/api/v1/opportunities/1");
  });
});
