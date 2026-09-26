import axios, { AxiosError } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { createLogger } from "@/lib/logger";
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "@/lib/secure-storage";

const logger = createLogger("api-client");

let dynamicPort: number | null = null;

function isTauriRuntime(): boolean {
  return (
    typeof window !== "undefined" &&
    (window as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ !== undefined
  );
}

export function setBackendPort(port: number) {
  dynamicPort = port;
  apiClient.defaults.baseURL = getBaseUrl();
  logger.info(`API client updated to port ${port}`);
}

function getBaseUrl(): string {
  if (dynamicPort) {
    return `http://127.0.0.1:${dynamicPort}`;
  }
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || "http://localhost:8000";
  }
  if (isTauriRuntime()) {
    return "http://127.0.0.1:8000";
  }
  return "http://localhost:8000";
}

let adapterReadyPromise: Promise<void> | null = null;

// Waits until the API client can actually reach the backend: the custom Tauri
// HTTP adapter must be installed (it resolves the real random port per request)
// AND the backend port must be known. Auth/session calls that run during the
// very first React render must await this, otherwise they can fire before the
// adapter is ready and target the stale default port (8000).
export function ensureApiReady(timeoutMs = 20000): Promise<void> {
  if (!isTauriRuntime()) return Promise.resolve();

  if (!adapterReadyPromise) {
    adapterReadyPromise = (async () => {
      const deadline = Date.now() + timeoutMs;
      while (Date.now() < deadline) {
        if (apiClient.defaults.adapter) {
          await ensureBackendPort(timeoutMs);
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      throw new Error("API client not ready: Tauri HTTP adapter did not initialize");
    })().finally(() => {
      adapterReadyPromise = null;
    });
  }
  return adapterReadyPromise;
}

let backendPortPromise: Promise<number> | null = null;

// Resolves the real backend port from the Rust side. The desktop backend is
// spawned on a RANDOM free port (never the fixed 8000), so every caller must
// learn it from the backend process. This retries until the port is published.
export function ensureBackendPort(timeoutMs = 20000): Promise<number> {
  if (dynamicPort) return Promise.resolve(dynamicPort);
  if (!isTauriRuntime()) return Promise.resolve(8000);

  if (!backendPortPromise) {
    backendPortPromise = (async () => {
      const deadline = Date.now() + timeoutMs;
      let lastError: unknown = new Error("Backend port not resolved");
      while (Date.now() < deadline) {
        try {
          const { invoke } = await import("@tauri-apps/api/core");
          const port = await invoke<number>("get_backend_port");
          if (port && port > 0) {
            setBackendPort(port);
            logger.info(`Backend port resolved from Rust: ${port}`);
            return port;
          }
        } catch (error) {
          lastError = error;
        }
        await new Promise((resolve) => setTimeout(resolve, 400));
      }
      logger.error("Timed out waiting for backend port", lastError);
      throw lastError instanceof Error ? lastError : new Error("Backend failed to start on time");
    })().finally(() => {
      backendPortPromise = null;
    });
  }
  return backendPortPromise;
}

function serializeHeaders(headers: Record<string, unknown>): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [key, value] of Object.entries(headers)) {
    if (typeof value === "string") {
      result[key] = value;
    }
  }
  return result;
}

type FetchLike = (
  url: string,
  init?: { method?: string; headers?: Record<string, string>; body?: BodyInit | null; signal?: AbortSignal | null },
) => Promise<Response>;

let cachedPluginFetch: FetchLike | null | undefined;

/** Lazily resolve the Tauri HTTP plugin fetch; null outside Tauri. Cached. */
async function getPluginFetch(): Promise<FetchLike | null> {
  if (cachedPluginFetch !== undefined) return cachedPluginFetch;
  try {
    const { fetch } = await import("@tauri-apps/plugin-http");
    cachedPluginFetch = fetch as unknown as FetchLike;
  } catch {
    cachedPluginFetch = null;
  }
  return cachedPluginFetch;
}

export async function createTauriAdapter(): Promise<typeof axios.defaults.adapter> {
  return async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
    await ensureBackendPort();
    const url = `${getBaseUrl()}${config.url || ""}`;
    const method = (config.method || "get").toUpperCase();

    const headers: Record<string, string> = {};
    if (config.headers) {
      Object.assign(headers, serializeHeaders(config.headers as Record<string, unknown>));
    }

    const isFormData = typeof FormData !== "undefined" && config.data instanceof FormData;

    let body: BodyInit | undefined;
    if (config.data && method !== "GET" && method !== "HEAD") {
      if (isFormData) {
        // Multipart upload: drop any Content-Type axios merged in (the JSON
        // instance default, or dispatchRequest's urlencoded fallback) so the
        // transport generates the correct multipart boundary. Any explicit
        // multipart value without a boundary breaks uploads in every build.
        body = config.data;
        const contentTypeKey = Object.keys(headers).find(
          (k) => k.toLowerCase() === "content-type",
        );
        if (contentTypeKey) delete headers[contentTypeKey];
      } else {
        body = typeof config.data === "string" ? config.data : JSON.stringify(config.data);
      }
    }

    let response: Response | undefined;
    // Custom adapters must enforce axios timeout themselves: abort the
    // request after config.timeout so hung requests surface as explicit
    // timeout errors instead of hanging forever.
    const timeoutMs = typeof config.timeout === "number" && config.timeout > 0 ? config.timeout : 0;
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timer = timeoutMs > 0 && controller
      ? setTimeout(() => controller.abort(new Error(`Request timed out after ${timeoutMs}ms: ${config.url || ""}`)), timeoutMs)
      : null;
    // Transport priority: native fetch (browser AND webview generate correct
    // multipart boundaries) → Tauri plugin fetch (no-CORS Rust client) →
    // global fetch fallback. Never send FormData through a transport that
    // forces a boundary-less Content-Type.
    const nativeFetch: FetchLike | null =
      typeof window !== "undefined" && typeof window.fetch === "function"
        ? window.fetch.bind(window)
        : null;
    const init = { method, headers, body, signal: controller?.signal ?? null };
    // Try each available transport in order until one returns a response.
    // Order per payload: FormData prefers native fetch (only it generates a
    // correct multipart boundary); JSON prefers the Tauri plugin (CORS-free
    // Rust client, preserving long-standing behavior and tests). A transport
    // that throws (missing runtime, network) falls through to the next one;
    // user aborts always propagate immediately. A cross-realm AbortSignal
    // (rejected by brand check) is retried once without the signal.
    const isSignalBrandError = (e: unknown) =>
      e instanceof Error && e.message.includes("AbortSignal");
    const runTransport = async (
      kind: "native" | "plugin" | "global",
      useSignal: boolean,
    ): Promise<Response | null> => {
      const attempt = useSignal ? init : { ...init, signal: null };
      if (kind === "native" && nativeFetch) return nativeFetch(url, attempt);
      if (kind === "plugin") {
        const pluginFetch = await getPluginFetch();
        if (pluginFetch) return pluginFetch(url, attempt);
        return null;
      }
      if (kind === "global" && typeof globalThis.fetch === "function") {
        return globalThis.fetch(url, attempt as RequestInit);
      }
      return null;
    };
    const order: Array<"native" | "plugin" | "global"> = isFormData
      ? ["native", "plugin", "global"]
      : ["plugin", "native", "global"];
    let lastError: unknown = new Error("No HTTP transport available");
    for (const kind of order) {
      try {
        const result = await runTransport(kind, true);
        if (result) {
          response = result;
          break;
        }
      } catch (err) {
        if (controller?.signal.aborted) throw err;
        if (isSignalBrandError(err)) {
          try {
            const retry = await runTransport(kind, false);
            if (retry) {
              response = retry;
              break;
            }
          } catch (err2) {
            if (controller?.signal.aborted) throw err2;
            lastError = err2;
          }
        } else {
          lastError = err;
        }
      }
    }
    if (!response) {
      // Normalize plain (non-Error) rejections — the Tauri fetch wrapper
      // rejects with the raw Rust error string on network-level failures —
      // so interceptors/UI always see an Error with the real reason.
      throw lastError instanceof Error
        ? lastError
        : new Error(
            typeof lastError === "string"
              ? lastError
              : typeof lastError === "object" && lastError !== null && "message" in lastError
                ? String((lastError as { message: unknown }).message)
                : "Network request failed",
          );
    }
    // Transport succeeded: clear the timeout timer before response handling.
    if (timer) clearTimeout(timer);

    const responseText = await response.text();
    let data: unknown;
    try {
      data = JSON.parse(responseText);
    } catch {
      data = responseText;
    }

    const responseHeaders: Record<string, string> = {};
    if (response.headers && typeof response.headers.forEach === "function") {
      response.headers.forEach((value: string, key: string) => {
        responseHeaders[key] = value;
      });
    }

    const responsePayload: AxiosResponse = {
      data,
      status: response.status,
      statusText: response.statusText || "",
      headers: responseHeaders,
      config,
      request: undefined,
    };

    // Official axios adapters reject non-2xx via settle(); our custom adapter
    // must do the same or HTTP errors would silently "succeed" and the UI would
    // never surface the real backend error message (e.g. sign-up failures).
    const validateStatus = config.validateStatus ?? ((status: number) => status >= 200 && status < 300);
    if (!validateStatus(responsePayload.status)) {
      throw new AxiosError(
        `Request failed with status code ${responsePayload.status}`,
        responsePayload.status >= 400 && responsePayload.status < 500
          ? AxiosError.ERR_BAD_REQUEST
          : AxiosError.ERR_BAD_RESPONSE,
        config,
        undefined,
        responsePayload,
      );
    }

    return responsePayload;
  };
}

const apiClient = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Install the fetch-based adapter in every environment (Tauri webview AND
// plain browser). It is transport-correct for both JSON and multipart
// payloads, unlike axios's default XHR adapter combined with a global JSON
// Content-Type (which corrupts FormData and forces boundary-less fallbacks).
createTauriAdapter().then((adapter) => {
  apiClient.defaults.adapter = adapter;
  logger.info("Using fetch-based HTTP adapter");
}).catch((err) => {
  logger.error("HTTP adapter unavailable, using default adapter:", err);
});

let isRefreshing = false;
let pendingRequests: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

type RefreshOutcome =
  | { ok: true; token: string }
  | { ok: false; definitive: boolean };

async function refreshTokens(): Promise<RefreshOutcome> {
  const refreshToken = await getRefreshToken();
  // No stored refresh token: the session cannot be restored, so the caller
  // must route back to sign-in (same as before).
  if (!refreshToken) return { ok: false, definitive: true };

  try {
    const response = await apiClient.post("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token: newRefreshToken } = response.data;
    await setTokens({ accessToken: access_token, refreshToken: newRefreshToken });
    return { ok: true, token: access_token };
  } catch (error) {
    // Only destroy the saved session when the server definitively rejected the
    // refresh token (4xx). Transient failures (backend still starting, network
    // blip, 5xx) must NOT wipe valid stored tokens.
    if (isDefinitiveAuthRejection(error)) {
      await clearTokens();
      return { ok: false, definitive: true };
    }
    return { ok: false, definitive: false };
  }
}

// A request that the server actively rejects (4xx) means the credentials are
// invalid/expired. Network errors and 5xx mean the backend is unreachable,
// which is transient and must never trigger a session wipe.
function isDefinitiveAuthRejection(error: unknown): boolean {
  return error instanceof AxiosError && !!error.response && error.response.status >= 400 && error.response.status < 500;
}

/**
 * Guard against axios's default JSON Content-Type destroying FormData.
 *
 * axios's transformRequest converts FormData to a JSON string whenever the
 * merged headers contain `application/json` (our instance default). That
 * runs BEFORE any adapter, so the Tauri adapter would only ever receive
 * `"{}"` and the backend would 422 on the missing `file` part. Stripping
 * the header here lets every transport (browser XHR, webview fetch, Tauri
 * adapter) generate the correct multipart boundary instead.
 */
export function stripJsonContentTypeForFormData(config: {
  data?: unknown;
  headers?: { delete?: (name: string) => void } & Record<string, unknown>;
}): void {
  if (typeof FormData === "undefined" || !(config.data instanceof FormData)) return;
  const headers = config.headers;
  if (!headers) return;
  if (typeof headers.delete === "function") {
    headers.delete("Content-Type");
    headers.delete("content-type");
  } else {
    for (const key of Object.keys(headers)) {
      if (key.toLowerCase() === "content-type") delete headers[key];
    }
  }
}

apiClient.interceptors.request.use(
  async (config) => {
    stripJsonContentTypeForFormData(config);
    const token = await getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    logger.debug(`Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    logger.error("Request error:", error);
    return Promise.reject(error);
  },
);

apiClient.interceptors.response.use(
  (response) => {
    logger.debug(`Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    if (error.response) {
      const { status, config, data } = error.response;
      logger.error(`API Error ${status}:`, data);

      const isAuthEndpoint = typeof config.url === "string" && /\/auth\/(signup|signin|forgot-password|reset-password|resend-verification|refresh|google)/.test(config.url);

      if (status === 401 && !config._retry && !isAuthEndpoint) {
        config._retry = true;

        if (isRefreshing) {
          return new Promise<string>((resolve, reject) => {
            pendingRequests.push({ resolve, reject });
          }).then((token) => {
            config.headers.Authorization = `Bearer ${token}`;
            return apiClient(config);
          });
        }

        isRefreshing = true;
        const outcome = await refreshTokens();
        isRefreshing = false;

        if (outcome.ok) {
          pendingRequests.forEach((p) => p.resolve(outcome.token));
          pendingRequests = [];
          config.headers.Authorization = `Bearer ${outcome.token}`;
          return apiClient(config);
        }

        pendingRequests.forEach((p) => p.reject(new Error("Refresh failed")));
        pendingRequests = [];
        // Only route to sign-in when the server definitively rejected the
        // session (bad/expired refresh token). A transient refresh failure
        // (network blip, backend restarting, 5xx) must NOT log the user out:
        // the stored tokens are still valid for a later retry.
        if (!outcome.definitive) {
          return Promise.reject(error);
        }
        // AuthContext clears local state; ProtectedRoute then redirects through
        // the memory router. Reloading here remounts AuthProvider before async
        // token deletion completes and can restart the same expiry cycle.
        try {
          window.dispatchEvent(new CustomEvent("fixly:auth-expired"));
        } catch {
          // Ignore environments without DOM event support (for example tests).
        }
      }
    } else if (error.request) {
      logger.error("Network error: No response received");
    } else {
      logger.error("Request setup error:", error.message);
    }
    return Promise.reject(error);
  },
);

export default apiClient;
