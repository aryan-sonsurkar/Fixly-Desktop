import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";

interface MissionWidgetProps {
  mission: { content: string; context_summary?: Record<string, unknown> } | null;
  loading: boolean;
  onGenerate: () => void;
}

export function MissionWidget({ mission, loading, onGenerate }: MissionWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-semibold">Today's Mission</h3>
        </div>
        <Button variant="outline" size="sm" onClick={onGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate"}
        </Button>
      </div>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ) : mission ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm text-muted-foreground"
        >
          {mission.content}
        </motion.div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Generate your AI-powered daily mission with priorities, schedule, and warnings.
        </p>
      )}
    </div>
  );
}
