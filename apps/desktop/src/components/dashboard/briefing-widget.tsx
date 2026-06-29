import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";

interface BriefingWidgetProps {
  briefing: { content: string } | null;
  loading: boolean;
  onGenerate: () => void;
}

export function BriefingWidget({ briefing, loading, onGenerate }: BriefingWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
          <h3 className="text-sm font-semibold">AI Daily Briefing</h3>
        </div>
        <Button variant="outline" size="sm" onClick={onGenerate} disabled={loading}>
          {loading ? "Generating..." : "Refresh"}
        </Button>
      </div>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      ) : briefing ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm text-muted-foreground"
        >
          {briefing.content}
        </motion.div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Generate your AI-powered daily briefing to start the day.
        </p>
      )}
    </div>
  );
}
