import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { StartupScreen } from "@/components/startup-screen";
import { version as packageVersion } from "../../../package.json";

const mockGetVersion = vi.fn();

vi.mock("@tauri-apps/api/app", () => ({
  getVersion: (...args: unknown[]) => mockGetVersion(...args),
}));

const originalTauri = (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;

describe("StartupScreen version", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ = originalTauri;
  });

  it("shows the Tauri runtime version, never a hardcoded placeholder", async () => {
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ = {};
    mockGetVersion.mockResolvedValue("9.9.9");
    render(<StartupScreen status={null} onRetry={() => undefined} />);
    await waitFor(() => {
      expect(screen.getByText("v9.9.9")).toBeTruthy();
    });
    expect(mockGetVersion).toHaveBeenCalled();
    expect(screen.queryByText("v1.0.0")).toBeNull();
  });

  it("falls back to the bundled package version when the runtime API fails", async () => {
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ = {};
    mockGetVersion.mockRejectedValue(new Error("no tauri"));
    render(<StartupScreen status={null} onRetry={() => undefined} />);
    await waitFor(() => {
      expect(screen.getByText(`v${packageVersion}`)).toBeTruthy();
    });
    expect(screen.queryByText("v1.0.0")).toBeNull();
  });

  it("uses the bundled package version outside Tauri without calling the API", () => {
    delete (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
    render(<StartupScreen status={null} onRetry={() => undefined} />);
    expect(screen.getByText(`v${packageVersion}`)).toBeTruthy();
    expect(mockGetVersion).not.toHaveBeenCalled();
    expect(screen.queryByText("v1.0.0")).toBeNull();
  });
});
