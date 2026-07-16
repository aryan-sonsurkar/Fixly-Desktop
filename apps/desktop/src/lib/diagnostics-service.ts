import apiClient from "@/lib/api-client";
import { version } from "../../package.json";

export interface Diagnostics {
  version: string;
  timestamp: string;
  backend: {
    status: "healthy" | "unhealthy" | "checking";
    version?: string;
    uptime?: string;
    port?: number;
    error?: string;
  };
  supabase: {
    status: "healthy" | "unhealthy" | "checking";
    error?: string;
  };
  ai: {
    status: "healthy" | "unhealthy" | "unconfigured" | "checking";
    provider?: string;
    model?: string;
    installed?: boolean;
    running?: boolean;
    model_count?: number;
    models?: string[];
    error?: string;
  };
  database: {
    status: "healthy" | "unhealthy" | "checking";
    error?: string;
  };
  sync: {
    status: "healthy" | "unhealthy" | "checking";
    lastSync?: string;
    error?: string;
  };
  environment: string;
  os: string;
  build: string;
}

export async function getDiagnostics(): Promise<Diagnostics> {
  const result: Diagnostics = {
    version,
    timestamp: new Date().toISOString(),
    backend: { status: "checking" },
    supabase: { status: "checking" },
    ai: { status: "checking" },
    database: { status: "checking" },
    sync: { status: "checking" },
    environment: import.meta.env.DEV ? "Development" : "Production",
    os: navigator.platform || "Unknown",
    build: import.meta.env.VITE_BUILD_VERSION || version,
  };

  try {
    const healthRes = await apiClient.get("/api/v1/health", { timeout: 5000 });
    const health = healthRes.data;

    result.backend = {
      status: "healthy",
      version: health.version || "unknown",
      port: health.port,
    };

    result.supabase = {
      status: health.supabase === "connected" ? "healthy" : "unhealthy",
      error: health.supabase_error,
    };

    result.database = {
      status: health.database === "connected" ? "healthy" : "unhealthy",
      error: health.database_error,
    };

    result.ai = {
      status: health.ai === "available" ? "healthy" : health.ai === "unconfigured" ? "unconfigured" : "unhealthy",
      provider: health.ai_provider || "unknown",
      model: health.ai_model,
      installed: health.ollama_installed,
      running: health.ollama_running,
      model_count: health.ollama_model_count,
      models: health.ollama_models,
      error: health.ai_error,
    };

    result.sync = {
      status: health.sync === "healthy" ? "healthy" : "unhealthy",
      lastSync: health.last_sync,
      error: health.sync_error,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Connection failed";
    result.backend = { status: "unhealthy", error: message };
    result.supabase = { status: "unhealthy", error: "Backend unreachable" };
    result.database = { status: "unhealthy", error: "Backend unreachable" };
    result.ai = { status: "unhealthy", error: "Backend unreachable" };
    result.sync = { status: "unhealthy", error: "Backend unreachable" };
  }

  return result;
}
