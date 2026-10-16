import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("framer-motion", () => ({
  motion: { div: ({ children, ...props }: Record<string, unknown>) => <div {...props}>{children as never}</div> },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: () => ({ setAuth: vi.fn() }),
}));

vi.mock("@/lib/secure-storage", () => ({
  setTokens: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  default: { post: vi.fn(), get: vi.fn() },
}));

import apiClient from "@/lib/api-client";
import { AuthCallbackPage } from "@/pages/auth-callback";

const post = apiClient.post as unknown as ReturnType<typeof vi.fn>;
const get = apiClient.get as unknown as ReturnType<typeof vi.fn>;

function renderCallback(entry: string) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <AuthCallbackPage />
    </MemoryRouter>,
  );
}

describe("AuthCallbackPage OAuth code exchange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("exchanges ?code= through the backend and signs in", async () => {
    post.mockResolvedValueOnce({
      data: { access_token: "abc", refresh_token: "def", user: { id: "1", email: "g@x.com" } },
    });
    get.mockResolvedValueOnce({
      data: { id: "1", email: "g@x.com", profile: {}, user_metadata: {} },
    });
    renderCallback("/auth/callback?code=auth-code-123");
    await waitFor(() => {
      expect(post).toHaveBeenCalledWith("/api/v1/auth/google/callback", {
        code: "auth-code-123",
        redirect_uri: "http://localhost:3000/auth/callback",
      });
    });
    await waitFor(() => {
      expect(screen.getByText(/Sign in successful/)).toBeTruthy();
    });
  });

  it("shows an error when the provider returns one", async () => {
    renderCallback("/auth/callback?error=access_denied");
    await waitFor(() => {
      expect(screen.getByText(/Authentication Failed/)).toBeTruthy();
    });
    expect(post).not.toHaveBeenCalled();
  });
});
