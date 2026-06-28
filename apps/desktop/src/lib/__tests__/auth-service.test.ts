import { describe, it, expect, vi, beforeEach } from "vitest";

type MockPost = ReturnType<typeof vi.fn>;
type MockGet = ReturnType<typeof vi.fn>;

const mockPost: MockPost = vi.fn();
const mockGet: MockGet = vi.fn();

vi.mock("@/lib/api-client", () => ({
  default: {
    post: mockPost,
    get: mockGet,
  },
}));

describe("AuthService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("signs in with email and password", async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: "abc", refresh_token: "def", user: { id: "1", email: "test@test.com" } },
    });

    const { signIn } = await import("@/lib/auth-service");
    const result = await signIn("test@test.com", "password123");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/signin", {
      email: "test@test.com",
      password: "password123",
    });
    expect(result.access_token).toBe("abc");
    expect(result.user.email).toBe("test@test.com");
  });

  it("signs up with email, password, and optional full_name", async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: "abc", refresh_token: "def", user: { id: "2", email: "new@test.com" } },
    });

    const { signUp } = await import("@/lib/auth-service");
    const result = await signUp("new@test.com", "password123", "Test User");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/signup", {
      email: "new@test.com",
      password: "password123",
      full_name: "Test User",
    });
    expect(result.access_token).toBe("abc");
  });

  it("signs out", async () => {
    mockPost.mockResolvedValueOnce({ data: {} });

    const { signOut } = await import("@/lib/auth-service");
    await signOut();

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/signout");
  });

  it("refreshes token", async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: "new-access", refresh_token: "new-refresh", user: { id: "1", email: "test@test.com" } },
    });

    const { refreshToken } = await import("@/lib/auth-service");
    const result = await refreshToken("old-refresh");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/refresh", { refresh_token: "old-refresh" });
    expect(result.access_token).toBe("new-access");
  });

  it("gets current user", async () => {
    mockGet.mockResolvedValueOnce({
      data: { id: "1", email: "test@test.com", profile: {}, user_metadata: {} },
    });

    const { getCurrentUser } = await import("@/lib/auth-service");
    const result = await getCurrentUser();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(result.id).toBe("1");
  });

  it("sends forgot password request", async () => {
    mockPost.mockResolvedValueOnce({ data: {} });

    const { forgotPassword } = await import("@/lib/auth-service");
    await forgotPassword("test@test.com");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/forgot-password", { email: "test@test.com" });
  });

  it("resets password", async () => {
    mockPost.mockResolvedValueOnce({ data: {} });

    const { resetPassword } = await import("@/lib/auth-service");
    await resetPassword("token-123", "NewPass123");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/reset-password", {
      access_token: "token-123",
      new_password: "NewPass123",
    });
  });

  it("gets Google auth URL", async () => {
    mockGet.mockResolvedValueOnce({ data: { url: "https://accounts.google.com/o/oauth2/auth" } });

    const { getGoogleAuthUrl } = await import("@/lib/auth-service");
    const url = await getGoogleAuthUrl();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/auth/google/url");
    expect(url).toBe("https://accounts.google.com/o/oauth2/auth");
  });

  it("handles Google callback", async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: "abc", refresh_token: "def", user: { id: "1" } },
    });

    const { googleCallback } = await import("@/lib/auth-service");
    const result = await googleCallback("code-xyz", "fixly://auth/callback");

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/google/callback", {
      code: "code-xyz",
      redirect_uri: "fixly://auth/callback",
    });
    expect(result.access_token).toBe("abc");
  });
});
