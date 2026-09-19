import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";
import type { DailyBriefing } from "@/lib/planner-service";

interface BriefingWidgetProps {
  briefing: DailyBriefing | null;
  loading: boolean;
  onGenerate: () => void;
  onNextStep?: () => void;
}

const priorityStyles: Record<string, string> = {
  urgent: "bg-red-500/10 text-red-600",
  high: "bg-amber-500/10 text-amber-600",
  medium: "bg-primary/10 text-primary",
  low: "bg-muted text-muted-foreground",
};

export function BriefingWidget({ briefing, loading, onGenerate, onNextStep }: BriefingWidgetProps) {
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
          {loading ? "Preparing..." : "Refresh"}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2" aria-label="Preparing your day">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <p className="pt-1 text-xs text-muted-foreground">Preparing your day...</p>
        </div>
      ) : briefing ? (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div>
            <p className="text-sm font-medium">{briefing.greeting}</p>
            <p className="mt-1 text-sm text-muted-foreground">{briefing.summary}</p>
          </div>

          {briefing.focus_items.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Today&apos;s Focus
              </p>
              <ol className="space-y-1.5">
                {briefing.focus_items.slice(0, 5).map((item, i) => (
                  <li key={`${item.title}-${i}`} className="flex items-start gap-2.5 text-sm">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
                      {i + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{item.title}</span>
                      <span className="text-xs text-muted-foreground">
                        {item.start_time} – {item.end_time}
                      </span>
                    </span>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${priorityStyles[item.priority] ?? priorityStyles.medium}`}>
                      {item.priority}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div className="rounded-lg border-l-2 border-primary/40 bg-muted/40 px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Quote of the day</p>
            <p className="mt-0.5 text-sm italic">&ldquo;{briefing.quote.text}&rdquo;</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">— {briefing.quote.attribution}</p>
          </div>

          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Today&apos;s motivation
            </p>
            <p className="text-sm text-muted-foreground">{briefing.motivation}</p>
          </div>

          <div className="flex items-center gap-2">
            {briefing.next_action && (
              <Button size="sm" onClick={onNextStep}>
                {briefing.next_action.label}
              </Button>
            )}
            {!briefing.ai_available && (
              <span className="text-[11px] text-muted-foreground">
                Generated from your schedule — AI was unavailable.
              </span>
            )}
          </div>
        </motion.div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Generate your AI-powered daily briefing to start the day.
        </p>
      )}
    </div>
  );
}
