import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("framer-motion", () => ({
  motion: { div: ({ children, ...props }: Record<string, unknown>) => <div {...props}>{children as never}</div> },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ signIn: vi.fn(), signUp: vi.fn(), isAuthenticated: false }),
}));

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (sel: (s: { setAuth: () => void }) => unknown) => sel({ setAuth: vi.fn() }),
}));

vi.mock("@/lib/secure-storage", () => ({
  listProfiles: vi.fn(),
  restoreProfile: vi.fn(),
  setTokens: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  default: { post: vi.fn(), get: vi.fn() },
}));

vi.mock("@/lib/auth-service", () => ({
  getGoogleAuthStatus: vi.fn().mockResolvedValue({ enabled: false }),
}));

import apiClient from "@/lib/api-client";
import { listProfiles, restoreProfile } from "@/lib/secure-storage";
import { RegisterPage } from "@/pages/register";

const post = apiClient.post as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
}

describe("RegisterPage saved-profile restore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (listProfiles as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([
      { email: "a@x.com", name: "A" },
      { email: "b@x.com", name: "B" },
    ]);
    (restoreProfile as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      accessToken: "a",
      refreshToken: "r",
    });
  });

  it("definitive refresh rejection tells the user the profile is unusable", async () => {
    post.mockRejectedValue({ response: { status: 401, data: {} } });
    renderPage();
    fireEvent.click(await screen.findByText("a@x.com"));
    await waitFor(() => {
      expect(screen.getByText(/Could not restore this profile/)).toBeTruthy();
    });
  });

  it("transient network failure preserves the profile and says to retry", async () => {
    post.mockRejectedValue(new Error("Network Error"));
    renderPage();
    fireEvent.click(await screen.findByText("a@x.com"));
    await waitFor(() => {
      expect(screen.getByText(/Couldn't reach Fixly/)).toBeTruthy();
    });
    expect(screen.queryByText(/Could not restore this profile/)).toBeNull();
  });
});
