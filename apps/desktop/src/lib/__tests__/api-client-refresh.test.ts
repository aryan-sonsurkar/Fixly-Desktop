import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
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

import apiClient from "@/lib/api-client";

type ResponseInterceptor = {
  rejected: (error: unknown) => Promise<AxiosResponse>;
};

describe("refresh storm regression", () => {
  it("emits auth expiry without reloading the Tauri window", async () => {
    const refresh = vi.spyOn(apiClient, "post").mockRejectedValue(new Error("refresh rejected"));
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
