import axios from "axios";
import { createLogger } from "@/lib/logger";
import { getAccessToken, clearTokens } from "@/lib/secure-storage";

const logger = createLogger("api-client");

function getBaseUrl(): string {
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || "http://localhost:8000";
  }
  return "http://127.0.0.1:8000";
}

const apiClient = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

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
      const { status, data } = error.response;
      logger.error(`API Error ${status}:`, data);

      if (status === 401) {
        await clearTokens();
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
