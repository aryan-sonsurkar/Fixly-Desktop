import { motion } from "framer-motion";
import { Skeleton } from "@fixly/ui";

interface HealthWidgetProps {
  score: number;
  riskLevel: string;
  loading: boolean;
  onRefresh: () => void;
}

export function HealthWidget({ score, riskLevel, loading, onRefresh }: HealthWidgetProps) {
  const scoreColor = score >= 70 ? "text-emerald-500" : score >= 40 ? "text-yellow-500" : "text-red-500";
  const ringColor = score >= 70 ? "stroke-emerald-500" : score >= 40 ? "stroke-yellow-500" : "stroke-red-500";
  const riskBadge = {
    Low: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    Medium: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    High: "bg-red-500/10 text-red-500 border-red-500/20",
  }[riskLevel] || "bg-muted text-muted-foreground";

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <h3 className="text-sm font-semibold">Academic Health</h3>
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
        <div className="flex items-center justify-center py-4">
          <Skeleton className="h-24 w-24 rounded-full" />
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-3"
        >
          <div className="relative h-24 w-24">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/20" />
              <circle
                cx="50" cy="50" r="42" fill="none" strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 42}`}
                strokeDashoffset={`${2 * Math.PI * 42 * (1 - score / 100)}`}
                strokeLinecap="round"
                className={ringColor}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-xl font-bold ${scoreColor}`}>{score}</span>
            </div>
          </div>
          <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${riskBadge}`}>
            {riskLevel} Risk
          </span>
        </motion.div>
      )}
    </div>
  );
}
