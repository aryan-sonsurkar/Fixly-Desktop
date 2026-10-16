import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api-client", () => ({
  default: { post: vi.fn(), get: vi.fn() },
}));

import apiClient from "@/lib/api-client";
import { ResetPasswordPage } from "@/pages/reset-password";

const post = apiClient.post as unknown as ReturnType<typeof vi.fn>;

function renderPage(entry = "/reset-password") {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <ResetPasswordPage />
    </MemoryRouter>,
  );
}

describe("ResetPasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("prefills the token from the query string", async () => {
    renderPage("/reset-password?token=recovery-abc");
    await waitFor(() => {
      expect((screen.getByPlaceholderText(/Paste from your reset email/) as HTMLInputElement).value).toBe(
        "recovery-abc"
      );
    });
  });

  it("rejects short and mismatched passwords without calling the API", async () => {
    renderPage("/reset-password?token=recovery-abc");
    fireEvent.change(screen.getByPlaceholderText("At least 8 characters"), { target: { value: "short" } });
    fireEvent.change(screen.getByPlaceholderText("Repeat your new password"), { target: { value: "short" } });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    await waitFor(() => {
      expect(screen.getByText("New password must be at least 8 characters.")).toBeTruthy();
    });
    expect(post).not.toHaveBeenCalled();
  });

  it("submits the new password with the token", async () => {
    post.mockResolvedValueOnce({ data: { message: "Password reset successfully" } });
    renderPage("/reset-password?token=recovery-abc");
    fireEvent.change(screen.getByPlaceholderText("At least 8 characters"), {
      target: { value: "new-password-123" },
    });
    fireEvent.change(screen.getByPlaceholderText("Repeat your new password"), {
      target: { value: "new-password-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    await waitFor(() => {
      expect(post).toHaveBeenCalledWith("/api/v1/auth/reset-password", {
        access_token: "recovery-abc",
        new_password: "new-password-123",
      });
    });
    await waitFor(() => {
      expect(screen.getByText(/Password updated/)).toBeTruthy();
    });
  });
});
