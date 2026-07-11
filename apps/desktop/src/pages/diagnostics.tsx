import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import { getDiagnostics, type Diagnostics } from "@/lib/diagnostics-service";
import { useAnalyticsStore } from "@/stores/analytics-store";

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

export function DiagnosticsPage() {
  const [data, setData] = useState<Diagnostics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
          <Button variant="outline" size="sm" onClick={runDiagnostics} disabled={loading}>
            {loading ? "Running..." : "Refresh"}
          </Button>
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
            detail={data?.backend.version ? `v${data.backend.version}` : undefined}
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
        <StatusRow label="AI Provider" status={data?.ai.status || "checking"} detail={data?.ai.provider} />
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

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Browser / Runtime</h2>
        <div className="space-y-2">
          <InfoRow label="User Agent" value={navigator.userAgent.substring(0, 80)} />
          <InfoRow label="Platform" value={navigator.platform} />
          <InfoRow label="Language" value={navigator.language} />
          <InfoRow label="Online" value={navigator.onLine ? "Yes" : "No"} />
        </div>
      </section>
    </div>
  );
}
