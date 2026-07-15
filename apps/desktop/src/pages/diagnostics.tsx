import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import { getDiagnostics, type Diagnostics } from "@/lib/diagnostics-service";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { createLogger } from "@/lib/logger";

const logger = createLogger("diagnostics-page");

const statusColors = {
  healthy: "text-success",
  unhealthy: "text-destructive",
  unconfigured: "text-muted-foreground",
  checking: "text-muted-foreground animate-pulse",
} as const;

function StatusDot({ status }: { status: keyof typeof statusColors }) {
  return (
    <span className={`inline-block h-2 w-2 rounded-full ${statusColors[status].replace("text-", "bg-")}`} />
  );
}

function StatusRow({ label, status, detail }: { label: string; status: keyof typeof statusColors; detail?: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-4 py-3">
      <div className="flex items-center gap-3">
        <StatusDot status={status} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <span className={`text-sm ${statusColors[status]}`}>
        {detail || status}
      </span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-muted/30 px-4 py-2.5">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function formatDiagnosticsText(data: Diagnostics): string {
  const lines = [
    "=== Fixly Diagnostics ===",
    `Generated: ${new Date(data.timestamp).toLocaleString()}`,
    "",
    "--- Application ---",
    `Version: ${data.version}`,
    `Build: ${data.build}`,
    `Environment: ${data.environment}`,
    `OS: ${data.os}`,
    "",
    "--- Backend ---",
    `Status: ${data.backend.status}`,
    data.backend.version ? `Version: ${data.backend.version}` : "",
    data.backend.port ? `Port: ${data.backend.port}` : "",
    data.backend.error ? `Error: ${data.backend.error}` : "",
    "",
    "--- Supabase ---",
    `Status: ${data.supabase.status}`,
    data.supabase.error ? `Error: ${data.supabase.error}` : "",
    "",
    "--- Database ---",
    `Status: ${data.database.status}`,
    data.database.error ? `Error: ${data.database.error}` : "",
    "",
    "--- AI Provider ---",
    `Status: ${data.ai.status}`,
    data.ai.provider ? `Provider: ${data.ai.provider}` : "",
    data.ai.model ? `Model: ${data.ai.model}` : "",
    data.ai.installed !== undefined ? `Ollama Installed: ${data.ai.installed}` : "",
    data.ai.running !== undefined ? `Ollama Running: ${data.ai.running}` : "",
    data.ai.model_count !== undefined ? `Models: ${data.ai.model_count}` : "",
    data.ai.error ? `Error: ${data.ai.error}` : "",
    "",
    "--- Sync ---",
    `Status: ${data.sync.status}`,
    data.sync.lastSync ? `Last Sync: ${data.sync.lastSync}` : "",
    data.sync.error ? `Error: ${data.sync.error}` : "",
    "",
  ];
  return lines.filter((l) => l !== "").join("\n");
}

export function DiagnosticsPage() {
  const [data, setData] = useState<Diagnostics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const events = useAnalyticsStore((s) => s.events);
  const appLaunches = useAnalyticsStore((s) => s.appLaunches);
  const sessionCount = useAnalyticsStore((s) => s.sessionCount);

  const runDiagnostics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDiagnostics();
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Diagnostics failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runDiagnostics();
  }, [runDiagnostics]);

  const handleCopy = useCallback(async () => {
    if (!data) return;
    try {
      await navigator.clipboard.writeText(formatDiagnosticsText(data));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      logger.error("Failed to copy diagnostics", err);
    }
  }, [data]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const text = formatDiagnosticsText(data);
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fixly-diagnostics-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [data]);

  const errorEvents = events.filter((e) => e.name === "error" || e.name === "api_error");
  const lastErrors = errorEvents.slice(-5).reverse();

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Diagnostics</h1>
            <p className="text-sm text-muted-foreground">System health and debug information</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCopy} disabled={!data || loading}>
              {copied ? "Copied!" : "Copy Diagnostics"}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport} disabled={!data || loading}>
              Export Diagnostics
            </Button>
            <Button variant="outline" size="sm" onClick={runDiagnostics} disabled={loading}>
              {loading ? "Running..." : "Refresh"}
            </Button>
          </div>
        </div>
      </motion.div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Application</h2>
        <div className="space-y-2">
          <InfoRow label="Version" value={data?.version || "loading..."} />
          <InfoRow label="Build" value={data?.build || "loading..."} />
          <InfoRow label="Environment" value={data?.environment || "loading..."} />
          <InfoRow label="Operating System" value={data?.os || "loading..."} />
          <InfoRow label="App Launches" value={String(appLaunches)} />
          <InfoRow label="Sessions" value={String(sessionCount)} />
          <InfoRow label="Events Tracked" value={String(events.length)} />
          <InfoRow label="Last Check" value={data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "never"} />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Services</h2>
        <div className="space-y-1">
          <StatusRow
            label="Backend API"
            status={data?.backend.status || "checking"}
            detail={
              data?.backend.port
                ? `:${data.backend.port}${data.backend.version ? ` (v${data.backend.version})` : ""}`
                : data?.backend.version
                  ? `v${data.backend.version}`
                  : undefined
            }
          />
          {data?.backend.uptime && (
            <div className="px-4 text-xs text-muted-foreground">Uptime: {data.backend.uptime}</div>
          )}
          {data?.backend.error && (
            <div className="px-4 text-xs text-destructive">{data.backend.error}</div>
          )}
        </div>
        <StatusRow label="Supabase" status={data?.supabase.status || "checking"} detail={data?.supabase.error} />
        <StatusRow label="Database" status={data?.database.status || "checking"} detail={data?.database.error} />
        <StatusRow
          label="AI Provider"
          status={data?.ai.status || "checking"}
          detail={data?.ai.provider ? `${data.ai.provider}${data.ai.model ? ` (${data.ai.model})` : ""}` : undefined}
        />
        {data?.ai.installed !== undefined && (
          <div className="px-4 text-xs text-muted-foreground">
            Ollama: {data.ai.installed ? "Installed" : "Not installed"}
            {data.ai.running !== undefined && ` · ${data.ai.running ? "Running" : "Not running"}`}
            {data.ai.model_count !== undefined && ` · ${data.ai.model_count} models`}
          </div>
        )}
        <StatusRow label="Sync" status={data?.sync.status || "checking"} />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recent Errors</h2>
        {lastErrors.length > 0 ? (
          <div className="space-y-2">
            {lastErrors.map((e, i) => (
              <div key={i} className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-destructive">
                    {e.properties?.context as string || "unknown"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {e.properties?.message as string || e.name}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No errors recorded this session.</p>
        )}
      </section>
    </div>
  );
}
