import { motion } from "framer-motion";
import { Skeleton } from "@fixly/ui";

interface Alert {
  type: string;
  message: string;
  action: string;
}

interface RiskAlertsWidgetProps {
  alerts: Alert[];
  loading: boolean;
  onRefresh: () => void;
}

export function RiskAlertsWidget({ alerts, loading, onRefresh }: RiskAlertsWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          <h3 className="text-sm font-semibold">Risk Alerts</h3>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent transition-colors"
          title="Refresh"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
          </svg>
        </button>
      </div>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : alerts.length > 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
          {alerts.map((alert, i) => {
            const colors = {
              critical: "border-red-500/30 bg-red-500/5",
              warning: "border-amber-500/30 bg-amber-500/5",
              info: "border-blue-500/30 bg-blue-500/5",
            }[alert.type] || "border-muted bg-muted/5";
            const icons = {
              critical: "text-red-500",
              warning: "text-amber-500",
              info: "text-blue-500",
            };
            return (
              <div key={i} className={`rounded-lg border p-3 ${colors}`}>
                <div className="flex items-start gap-2">
                  <svg className={`mt-0.5 h-4 w-4 flex-shrink-0 ${icons[alert.type] || "text-muted-foreground"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium">{alert.message}</p>
                    <p className="mt-0.5 text-[10px] text-muted-foreground">{alert.action}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </motion.div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-4 text-center">
          <svg className="h-8 w-8 text-emerald-500/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-muted-foreground">No active alerts</p>
        </div>
      )}
    </div>
  );
}
