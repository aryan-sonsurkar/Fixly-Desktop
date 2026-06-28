import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@tauri-apps/plugin-store", () => ({
  load: vi.fn().mockRejectedValue(new Error("Tauri not available")),
}));

describe("SecureStorage (in-memory fallback)", () => {
  beforeEach(async () => {
    const { clearTokens } = await import("@/lib/secure-storage");
    await clearTokens();
  });

  it("returns null when no tokens are stored", async () => {
    const { getAccessToken, getRefreshToken } = await import("@/lib/secure-storage");
    expect(await getAccessToken()).toBeNull();
    expect(await getRefreshToken()).toBeNull();
  });

  it("stores and retrieves tokens", async () => {
    const { setTokens, getAccessToken, getRefreshToken } = await import("@/lib/secure-storage");
    await setTokens({ accessToken: "access-123", refreshToken: "refresh-456" });

    expect(await getAccessToken()).toBe("access-123");
    expect(await getRefreshToken()).toBe("refresh-456");
  });

  it("clears tokens", async () => {
    const { setTokens, clearTokens, getAccessToken } = await import("@/lib/secure-storage");
    await setTokens({ accessToken: "access-123", refreshToken: "refresh-456" });
    await clearTokens();

    expect(await getAccessToken()).toBeNull();
  });

  it("restores session when both tokens exist", async () => {
    const { setTokens, restoreSession } = await import("@/lib/secure-storage");
    await setTokens({ accessToken: "access-123", refreshToken: "refresh-456" });

    const session = await restoreSession();
    expect(session).not.toBeNull();
    expect(session!.accessToken).toBe("access-123");
    expect(session!.refreshToken).toBe("refresh-456");
  });

  it("returns null from restoreSession when no tokens exist", async () => {
    const { restoreSession } = await import("@/lib/secure-storage");
    expect(await restoreSession()).toBeNull();
  });
});
