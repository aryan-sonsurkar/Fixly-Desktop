import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("framer-motion", () => ({
  motion: { div: ({ children, ...props }: Record<string, unknown>) => <div {...props}>{children as never}</div> },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockSignIn = vi.fn();
const mockSignUp = vi.fn();

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ signIn: mockSignIn, signUp: mockSignUp, isAuthenticated: false }),
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
  forgotPassword: vi.fn().mockResolvedValue({ message: "Password reset email sent" }),
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

describe("RegisterPage password authentication", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (listProfiles as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });

  it("signup submits a chosen password to signUp", async () => {
    mockSignUp.mockResolvedValueOnce(undefined);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText("John Doe"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "new@x.com" } });
    fireEvent.change(screen.getByPlaceholderText("At least 8 characters"), { target: { value: "password123" } });
    fireEvent.change(screen.getByPlaceholderText("Repeat your password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith("new@x.com", "password123", "Test User");
    });
  });

  it("signup without a password creates a passwordless account", async () => {
    mockSignUp.mockResolvedValueOnce(undefined);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText("John Doe"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "nopass@x.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith("nopass@x.com", undefined, "Test User");
    });
  });

  it("signup rejects mismatched passwords before submitting", async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText("John Doe"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "new@x.com" } });
    fireEvent.change(screen.getByPlaceholderText("At least 8 characters"), { target: { value: "password123" } });
    fireEvent.change(screen.getByPlaceholderText("Repeat your password"), { target: { value: "different456" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() => {
      expect(screen.getByText("Passwords do not match")).toBeTruthy();
    });
    expect(mockSignUp).not.toHaveBeenCalled();
  });

  it("forgot password sends a reset email", async () => {
    const { forgotPassword } = await import("@/lib/auth-service");
    renderPage();
    fireEvent.click(screen.getByText("Sign in"));
    fireEvent.click(await screen.findByText("Forgot password?"));
    fireEvent.change(screen.getByLabelText("Reset your password"), { target: { value: "user@x.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Send reset email" }));
    await waitFor(() => {
      expect(forgotPassword as unknown as ReturnType<typeof vi.fn>).toHaveBeenCalledWith("user@x.com");
    });
    await waitFor(() => {
      expect(screen.getByText(/Reset email sent/)).toBeTruthy();
    });
  });
});
