import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

// Mock Tauri plugin-updater and api/core before importing the hook
const mockCheck = vi.fn();
const mockInvoke = vi.fn(async () => {});

vi.mock("@tauri-apps/plugin-updater", () => ({
  check: mockCheck,
}));

vi.mock("@tauri-apps/api/core", () => ({
  invoke: mockInvoke,
}));

// Ensure window.__TAURI_INTERNALS__ is present so isTauri() returns true
const originalTauri = (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;

import { useUpdater } from "@/hooks/useUpdater";

describe("useUpdater — backend shutdown before install", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ = {};
    mockInvoke.mockResolvedValue(undefined);
    mockCheck.mockResolvedValue({
      version: "1.0.1",
      body: "notes",
      date: new Date().toISOString(),
      downloadAndInstall: vi.fn(async () => {}),
    });
  });

  afterEach(() => {
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ = originalTauri;
  });

  it("invokes shutdown_backend before downloadAndInstall", async () => {
    const { result } = renderHook(() => useUpdater());

    // Drive to available state via check
    await act(async () => {
      await result.current.check();
    });
    expect(result.current.state.status).toBe("available");

    mockInvoke.mockClear();
    mockCheck.mockClear();

    // Prepare next check inside downloadAndInstall to return an update again
    const downloadAndInstall = vi.fn(async (_cb?: unknown) => {});
    mockCheck.mockResolvedValue({
      version: "1.0.1",
      body: null,
      date: null,
      downloadAndInstall,
    });

    await act(async () => {
      await result.current.downloadAndInstall();
    });

    // shutdown_backend must have been invoked before the second check/download
    expect(mockInvoke).toHaveBeenCalledWith("shutdown_backend");
    // The second check should still have been attempted
    expect(mockCheck).toHaveBeenCalled();
  });

  it("proceeds with update even if shutdown_backend fails", async () => {
    const { result } = renderHook(() => useUpdater());
    await act(async () => { await result.current.check(); });
    expect(result.current.state.status).toBe("available");

    mockInvoke.mockRejectedValueOnce(new Error("shutdown failed: not found"));
    const downloadAndInstall = vi.fn(async () => {});
    mockCheck.mockResolvedValue({
      version: "1.0.1",
      body: null,
      date: null,
      downloadAndInstall,
    } as unknown as Awaited<ReturnType<typeof mockCheck>>);

    await act(async () => {
      await result.current.downloadAndInstall();
    });

    // Despite shutdown failure, download should have been attempted and state should not be error
    expect(downloadAndInstall).toHaveBeenCalled();
    expect(result.current.state.status).not.toBe("error");
  });

  it("retry remains intact after error", async () => {
    const { result } = renderHook(() => useUpdater());
    // Force check to error via mock
    mockCheck.mockRejectedValueOnce(new Error("network offline"));
    await act(async () => { await result.current.check(); });
    expect(result.current.state.status).toBe("error");

    // Retry should reset to idle then re-check
    mockCheck.mockResolvedValueOnce(null as unknown as Awaited<ReturnType<typeof mockCheck>>);
    await act(async () => { result.current.retry(); });
    await waitFor(() => expect(result.current.state.status).toBe("up_to_date"));
  });
});
