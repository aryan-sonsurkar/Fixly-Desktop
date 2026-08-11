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

export async function createTauriAdapter(): Promise<typeof axios.defaults.adapter> {
  const { fetch } = await import("@tauri-apps/plugin-http");

  return async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
    await ensureBackendPort();
    const url = `${getBaseUrl()}${config.url || ""}`;
    const method = (config.method || "get").toUpperCase();

    const headers: Record<string, string> = {};
    if (config.headers) {
      Object.assign(headers, serializeHeaders(config.headers as Record<string, unknown>));
    }

    let body: string | undefined;
    if (config.data && method !== "GET" && method !== "HEAD") {
      body = typeof config.data === "string" ? config.data : JSON.stringify(config.data);
    }

    let response;
    try {
      response = await fetch(url, {
        method,
        headers,
        body,
      });
    } catch (error) {
      // The Tauri fetch wrapper rejects with a plain (non-Error) value on
      // network-level failures (often the raw Rust error string); normalize it
      // so interceptors/UI always see an Error with the real reason.
      throw error instanceof Error
        ? error
        : new Error(
            typeof error === "string"
              ? error
              : typeof error === "object" && error !== null && "message" in error
                ? String((error as { message: unknown }).message)
                : "Network request failed",
          );
    }

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

const isTauri = isTauriRuntime();

if (isTauri) {
  createTauriAdapter().then((adapter) => {
    apiClient.defaults.adapter = adapter;
    logger.info("Using Tauri HTTP plugin adapter (CORS bypass)");
  }).catch((err) => {
    logger.error("Tauri HTTP plugin unavailable, using default adapter:", err);
  });
}

let isRefreshing = false;
let pendingRequests: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

async function refreshTokens(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await apiClient.post("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token: newRefreshToken } = response.data;
    await setTokens({ accessToken: access_token, refreshToken: newRefreshToken });
    return access_token;
  } catch {
    await clearTokens();
    return null;
  }
}

apiClient.interceptors.request.use(
  async (config) => {
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
        const newToken = await refreshTokens();
        isRefreshing = false;

        if (newToken) {
          pendingRequests.forEach((p) => p.resolve(newToken));
          pendingRequests = [];
          config.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(config);
        }

        pendingRequests.forEach((p) => p.reject(new Error("Refresh failed")));
        pendingRequests = [];
        window.location.hash = "#/register";
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
