import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { AxiosError } from "axios";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/logger", () => ({
  createLogger: () => ({ debug: vi.fn(), error: vi.fn(), info: vi.fn(), warn: vi.fn() }),
}));

vi.mock("@/lib/secure-storage", () => ({
  getAccessToken: vi.fn().mockResolvedValue("expired-access-token"),
  getRefreshToken: vi.fn().mockResolvedValue("refresh-token"),
  setTokens: vi.fn().mockResolvedValue(undefined),
  clearTokens: vi.fn().mockResolvedValue(undefined),
}));

import { clearTokens, getRefreshToken } from "@/lib/secure-storage";
import apiClient from "@/lib/api-client";

type ResponseInterceptor = {
  rejected: (error: unknown) => Promise<AxiosResponse>;
};

describe("refresh storm regression", () => {
  it("emits auth expiry without reloading the Tauri window", async () => {
    // Definitive rejection (401 on the refresh call itself): session is dead.
    const refreshError = new AxiosError(
      "Request failed with status code 401",
      AxiosError.ERR_BAD_REQUEST,
      { url: "/api/v1/auth/refresh", headers: {} } as InternalAxiosRequestConfig,
      undefined,
      {
        data: { error: "Session expired. Please sign in again." },
        status: 401,
        statusText: "",
        headers: {},
        config: { url: "/api/v1/auth/refresh", headers: {} } as InternalAxiosRequestConfig,
      },
    );
    const refresh = vi.spyOn(apiClient, "post").mockRejectedValue(refreshError);
    const originalHash = window.location.hash;
    Object.defineProperty(window, "__TAURI_INTERNALS__", { configurable: true, value: {} });
    const expiredEvent = vi.fn();
    window.addEventListener("fixly:auth-expired", expiredEvent);

    const handlers = (apiClient.interceptors.response as unknown as { handlers: ResponseInterceptor[] }).handlers;
    const reject = handlers.at(-1)?.rejected;
    const error = {
      response: {
        status: 401,
        config: { url: "/api/v1/dashboard", headers: {} } as InternalAxiosRequestConfig,
        data: {},
      },
    };

    await expect(reject!(error)).rejects.toBe(error);

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(expiredEvent).toHaveBeenCalledTimes(1);
    expect(window.location.hash).toBe(originalHash);

    window.removeEventListener("fixly:auth-expired", expiredEvent);
    delete (window as Window & { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
  });

  it("does NOT emit auth expiry when the refresh call fails transiently", async () => {
    vi.mocked(clearTokens).mockClear();
    // Transient failure (network-level, no response): stored tokens stay valid.
    const refresh = vi.spyOn(apiClient, "post").mockRejectedValue(new Error("refresh rejected"));
    Object.defineProperty(window, "__TAURI_INTERNALS__", { configurable: true, value: {} });
    const expiredEvent = vi.fn();
    window.addEventListener("fixly:auth-expired", expiredEvent);

    const handlers = (apiClient.interceptors.response as unknown as { handlers: ResponseInterceptor[] }).handlers;
    const reject = handlers.at(-1)?.rejected;
    const error = {
      response: {
        status: 401,
        config: { url: "/api/v1/dashboard", headers: {} } as InternalAxiosRequestConfig,
        data: {},
      },
    };

    await expect(reject!(error)).rejects.toBe(error);

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(expiredEvent).not.toHaveBeenCalled();
    expect(vi.mocked(clearTokens)).not.toHaveBeenCalled();

    window.removeEventListener("fixly:auth-expired", expiredEvent);
    delete (window as Window & { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
  });

  it("emits auth expiry when no refresh token is stored", async () => {
    vi.mocked(getRefreshToken).mockResolvedValueOnce(null);
    const refresh = vi.spyOn(apiClient, "post");
    Object.defineProperty(window, "__TAURI_INTERNALS__", { configurable: true, value: {} });
    const expiredEvent = vi.fn();
    window.addEventListener("fixly:auth-expired", expiredEvent);

    const handlers = (apiClient.interceptors.response as unknown as { handlers: ResponseInterceptor[] }).handlers;
    const reject = handlers.at(-1)?.rejected;
    const error = {
      response: {
        status: 401,
        config: { url: "/api/v1/dashboard", headers: {} } as InternalAxiosRequestConfig,
        data: {},
      },
    };

    await expect(reject!(error)).rejects.toBe(error);

    // No refresh attempt possible without a stored token; must route to sign-in.
    expect(refresh).not.toHaveBeenCalled();
    expect(expiredEvent).toHaveBeenCalledTimes(1);

    window.removeEventListener("fixly:auth-expired", expiredEvent);
    delete (window as Window & { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
  });

  it("coalesces concurrent 401 responses into one refresh and retries every request", async () => {
    const refresh = vi.spyOn(apiClient, "post").mockResolvedValue({
      data: { access_token: "fresh-access-token", refresh_token: "fresh-refresh-token" },
    } as AxiosResponse);
    const adapter = vi.fn(async (config: InternalAxiosRequestConfig) => ({
      data: { ok: true },
      status: 200,
      statusText: "OK",
      headers: {},
      config,
    }));
    apiClient.defaults.adapter = adapter;

    const handlers = (apiClient.interceptors.response as unknown as { handlers: ResponseInterceptor[] }).handlers;
    const reject = handlers.at(-1)?.rejected;
    expect(reject).toBeDefined();

    const expiredRequest = (): { response: { status: number; config: InternalAxiosRequestConfig; data: object } } => ({
      response: {
        status: 401,
        config: { url: "/api/v1/dashboard", headers: {} } as InternalAxiosRequestConfig,
        data: {},
      },
    });

    const results = await Promise.all(Array.from({ length: 6 }, () => reject!(expiredRequest())));

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(adapter).toHaveBeenCalledTimes(6);
    expect(results).toHaveLength(6);
  });
});
