import { describe, it, expect, vi, beforeEach } from "vitest";

type MockFn = ReturnType<typeof vi.fn>;

const mockGet: MockFn = vi.fn();
const mockPost: MockFn = vi.fn();
const mockPut: MockFn = vi.fn();
const mockDelete: MockFn = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}));

describe("MemoryService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("listMemories fetches all memories", async () => {
    const mockMemories = [
      { id: "1", content: "Test memory", category: "fact", confidence: 0.8 },
    ];
    mockGet.mockResolvedValueOnce({ data: mockMemories });

    const { listMemories } = await import("@/lib/memory-service");
    const result = await listMemories();

    expect(result).toEqual(mockMemories);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/memory");
  });

  it("listMemories with category filter", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    const { listMemories } = await import("@/lib/memory-service");
    await listMemories({ category: "fact" });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/memory?category=fact");
  });

  it("listMemories with archived filter", async () => {
    mockGet.mockResolvedValueOnce({ data: [] });

    const { listMemories } = await import("@/lib/memory-service");
    await listMemories({ archived: true });

    expect(mockGet).toHaveBeenCalledWith("/api/v1/memory?archived=true");
  });

  it("getMemory fetches single memory", async () => {
    const mockMemory = { id: "1", content: "Test" };
    mockGet.mockResolvedValueOnce({ data: mockMemory });

    const { getMemory } = await import("@/lib/memory-service");
    const result = await getMemory("1");

    expect(result).toEqual(mockMemory);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/memory/1");
  });

  it("createMemory posts new memory", async () => {
    const mockMemory = { id: "1", content: "New memory" };
    mockPost.mockResolvedValueOnce({ data: mockMemory });

    const { createMemory } = await import("@/lib/memory-service");
    const result = await createMemory({ content: "New memory", category: "fact" });

    expect(result).toEqual(mockMemory);
    expect(mockPost).toHaveBeenCalledWith("/api/v1/memory", {
      content: "New memory",
      category: "fact",
    });
  });

  it("updateMemory puts changes", async () => {
    const mockMemory = { id: "1", content: "Updated" };
    mockPut.mockResolvedValueOnce({ data: mockMemory });

    const { updateMemory } = await import("@/lib/memory-service");
    const result = await updateMemory("1", { content: "Updated" });

    expect(result).toEqual(mockMemory);
    expect(mockPut).toHaveBeenCalledWith("/api/v1/memory/1", { content: "Updated" });
  });

  it("deleteMemory calls delete endpoint", async () => {
    mockDelete.mockResolvedValueOnce({});

    const { deleteMemory } = await import("@/lib/memory-service");
    await deleteMemory("1");

    expect(mockDelete).toHaveBeenCalledWith("/api/v1/memory/1");
  });

  it("archiveMemory posts archive", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "1", is_archived: true } });

    const { archiveMemory } = await import("@/lib/memory-service");
    await archiveMemory("1");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/memory/1/archive");
  });

  it("unarchiveMemory posts unarchive", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: "1", is_archived: false } });

    const { unarchiveMemory } = await import("@/lib/memory-service");
    await unarchiveMemory("1");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/memory/1/unarchive");
  });

  it("searchMemories posts query", async () => {
    mockPost.mockResolvedValueOnce({ data: [] });

    const { searchMemories } = await import("@/lib/memory-service");
    await searchMemories({ query: "math", top_k: 5 });

    expect(mockPost).toHaveBeenCalledWith("/api/v1/memory/search", {
      query: "math",
      top_k: 5,
    });
  });

  it("getMemoryStats fetches stats", async () => {
    const stats = { total_memories: 10, by_category: {}, by_source: {}, avg_confidence: 0.7 };
    mockGet.mockResolvedValueOnce({ data: stats });

    const { getMemoryStats } = await import("@/lib/memory-service");
    const result = await getMemoryStats();

    expect(result).toEqual(stats);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/memory/stats");
  });

  it("resetAllMemories posts reset", async () => {
    mockPost.mockResolvedValueOnce({ data: { deleted: 5 } });

    const { resetAllMemories } = await import("@/lib/memory-service");
    const result = await resetAllMemories();

    expect(result).toEqual({ deleted: 5 });
    expect(mockPost).toHaveBeenCalledWith("/api/v1/memory/reset", { confirmation: "RESET" });
  });
});
