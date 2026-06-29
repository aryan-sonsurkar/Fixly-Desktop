import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Badge } from "@fixly/ui";

interface DeadlinesWidgetProps {
  deadlines: Array<{
    title: string;
    due: string;
    priority: string;
    status?: string;
  }>;
  total: number;
  urgent: number;
}

function priorityColor(p: string): string {
  switch (p) {
    case "urgent": return "bg-red-500/10 text-red-500";
    case "high": return "bg-orange-500/10 text-orange-500";
    case "medium": return "bg-blue-500/10 text-blue-500";
    default: return "bg-gray-500/10 text-gray-500";
  }
}

export function DeadlinesWidget({ deadlines, total, urgent }: DeadlinesWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-sm font-semibold">Upcoming Assignments</h3>
        </div>
        <Link to="/assignments" className="text-xs text-primary hover:underline">
          View all ({total})
        </Link>
      </div>
      {urgent > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="mb-3 rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive"
        >
          {urgent} urgent deadline{urgent > 1 ? "s" : ""} need attention
        </motion.div>
      )}
      {deadlines.length === 0 ? (
        <p className="text-sm text-muted-foreground">No upcoming deadlines.</p>
      ) : (
        <div className="space-y-2">
          {deadlines.slice(0, 5).map((d, i) => (
            <motion.div
              key={d.title + i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2 text-sm"
            >
              <span className="truncate font-medium">{d.title}</span>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-muted-foreground">
                  {new Date(d.due).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </span>
                <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${priorityColor(d.priority)}`}>
                  {d.priority}
                </Badge>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
