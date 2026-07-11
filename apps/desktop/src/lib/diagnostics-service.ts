import apiClient from "@/lib/api-client";
import { version } from "../../package.json";

export interface Diagnostics {
  version: string;
  timestamp: string;
  backend: {
    status: "healthy" | "unhealthy" | "checking";
    version?: string;
    uptime?: string;
    error?: string;
  };
  supabase: {
    status: "healthy" | "unhealthy" | "checking";
    error?: string;
  };
  ai: {
    status: "healthy" | "unhealthy" | "unconfigured" | "checking";
    provider?: string;
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
  };

  try {
    const healthRes = await apiClient.get("/api/v1/health", { timeout: 5000 });
    const health = healthRes.data;

    result.backend = {
      status: "healthy",
      version: health.version || "unknown",
      uptime: health.uptime || health.uptime_seconds ? `${health.uptime_seconds}s` : undefined,
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
    result.ai = { status: "checking", error: "Backend unreachable" };
    result.sync = { status: "checking", error: "Backend unreachable" };
  }

  return result;
}
