import { describe, it, expect, vi, beforeEach } from "vitest";

type MockGet = ReturnType<typeof vi.fn>;
type MockPost = ReturnType<typeof vi.fn>;
type MockPut = ReturnType<typeof vi.fn>;
type MockDelete = ReturnType<typeof vi.fn>;

const mockGet: MockGet = vi.fn();
const mockPost: MockPost = vi.fn();
const mockPut: MockPut = vi.fn();
const mockDelete: MockDelete = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}));

const mockAssignment = {
  id: "1",
  user_id: "u1",
  subject_id: "s1",
  title: "Test Assignment",
  description: "A test assignment",
  status: "pending" as const,
  priority: "medium" as const,
  due_date: "2026-07-01T00:00:00Z",
  estimated_study_time: 60,
  tags: ["exam", "quiz"],
  notes: "Some notes",
  is_archived: false,
  is_pinned: false,
  is_favorite: false,
  source: "manual" as const,
  ai_draft: null,
  ai_draft_generated: false,
  created_at: "2026-06-01T00:00:00Z",
  updated_at: "2026-06-01T00:00:00Z",
};

describe("AssignmentService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches assignments with query parameters", async () => {
    const paginatedResponse = {
      data: [mockAssignment],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    mockGet.mockResolvedValueOnce({ data: paginatedResponse });

    const { getAssignments } = await import("@/lib/assignment-service");
    const result = await getAssignments({ status: "pending", page: 1, page_size: 20 });

    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining("/api/v1/assignments?"));
    expect(result.data).toHaveLength(1);
    expect(result.data[0].title).toBe("Test Assignment");
  });

  it("creates an assignment", async () => {
    mockPost.mockResolvedValueOnce({ data: mockAssignment });

    const { createAssignment } = await import("@/lib/assignment-service");
    const result = await createAssignment({ title: "Test Assignment", priority: "medium" });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/assignments", {
      title: "Test Assignment",
      priority: "medium",
    });
    expect(result.id).toBe("1");
  });

  it("updates an assignment", async () => {
    const updated = { ...mockAssignment, title: "Updated Title" };
    mockPut.mockResolvedValueOnce({ data: updated });

    const { updateAssignment } = await import("@/lib/assignment-service");
    const result = await updateAssignment("1", { title: "Updated Title" });

    expect(mockPut).toHaveBeenCalledWith("/api/v1/assignments/1", { title: "Updated Title" });
    expect(result.title).toBe("Updated Title");
  });

  it("deletes an assignment", async () => {
    mockDelete.mockResolvedValueOnce({ data: {} });

    const { deleteAssignment } = await import("@/lib/assignment-service");
    await deleteAssignment("1");

    expect(mockDelete).toHaveBeenCalledWith("/api/v1/assignments/1");
  });

  it("duplicates an assignment", async () => {
    mockPost.mockResolvedValueOnce({ data: mockAssignment });

    const { duplicateAssignment } = await import("@/lib/assignment-service");
    const result = await duplicateAssignment("1");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/assignments/1/duplicate");
    expect(result.id).toBe("1");
  });

  it("performs bulk action", async () => {
    mockPost.mockResolvedValueOnce({ data: { affected: 2, data: [mockAssignment] } });

    const { bulkAction } = await import("@/lib/assignment-service");
    const result = await bulkAction(["1", "2"], "complete");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/assignments/bulk", {
      ids: ["1", "2"],
      action: "complete",
      value: undefined,
    });
    expect(result.affected).toBe(2);
  });

  it("fetches assignment stats", async () => {
    const stats = {
      total: 10,
      completed: 5,
      pending: 3,
      in_progress: 1,
      overdue: 1,
      completion_percentage: 50,
      due_today: 2,
      due_this_week: 4,
      avg_completion_time_hours: null,
    };
    mockGet.mockResolvedValueOnce({ data: stats });

    const { getAssignmentStats } = await import("@/lib/assignment-service");
    const result = await getAssignmentStats();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/assignments/stats");
    expect(result.total).toBe(10);
    expect(result.completion_percentage).toBe(50);
  });
});
