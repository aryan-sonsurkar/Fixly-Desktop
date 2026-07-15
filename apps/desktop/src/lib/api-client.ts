import axios from "axios";
import { createLogger } from "@/lib/logger";
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "@/lib/secure-storage";

const logger = createLogger("api-client");

let dynamicPort: number | null = null;

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
  if (typeof window !== "undefined" && (window as { __TAURI__?: unknown }).__TAURI__) {
    return "http://127.0.0.1:8000";
  }
  return "http://localhost:8000";
}

const apiClient = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

let isRefreshing = false;
let pendingRequests: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

async function refreshTokens(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${getBaseUrl()}/api/v1/auth/refresh`, {
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
        window.location.hash = "#/login";
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
