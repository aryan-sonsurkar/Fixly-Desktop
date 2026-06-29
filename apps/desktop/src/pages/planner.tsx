import { useEffect } from "react";
import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";
import { usePlannerStore } from "@/stores/planner-store";
import { generateDailyPlan, generateWeeklyPlan, generateRevisionPlan } from "@/lib/planner-service";

export function PlannerPage() {
  const {
    dailyPlan, weeklyPlan, revisionPlan,
    loadingDaily, loadingWeekly, loadingRevision,
    activeView, setActiveView,
    setDailyPlan, setWeeklyPlan, setRevisionPlan,
    setLoadingDaily, setLoadingWeekly, setLoadingRevision,
  } = usePlannerStore();

  const generate = async () => {
    if (activeView === "daily") {
      setLoadingDaily(true);
      try { const p = await generateDailyPlan(); setDailyPlan(p); } catch { /* silently fail */ } finally { setLoadingDaily(false); }
    } else if (activeView === "weekly") {
      setLoadingWeekly(true);
      try { const p = await generateWeeklyPlan(); setWeeklyPlan(p); } catch { /* silently fail */ } finally { setLoadingWeekly(false); }
    } else {
      setLoadingRevision(true);
      try { const p = await generateRevisionPlan(); setRevisionPlan(p); } catch { /* silently fail */ } finally { setLoadingRevision(false); }
    }
  };

  useEffect(() => { if (!dailyPlan && !weeklyPlan && !revisionPlan) generate(); }, []);

  const currentPlan = activeView === "daily" ? dailyPlan : activeView === "weekly" ? weeklyPlan : revisionPlan;
  const isLoading = activeView === "daily" ? loadingDaily : activeView === "weekly" ? loadingWeekly : loadingRevision;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Study Planner</h1>
          <p className="text-sm text-muted-foreground">AI-powered study plans tailored to your workload</p>
        </div>
      </div>

      <div className="mb-6 flex gap-2">
        {(["daily", "weekly", "revision"] as const).map((view) => (
          <button
            key={view}
            type="button"
            onClick={() => setActiveView(view)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors capitalize ${
              activeView === view
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-accent"
            }`}
          >
            {view}
          </button>
        ))}
      </div>

      <div className="mb-6 flex gap-2">
        <Button onClick={generate} disabled={isLoading} size="sm">
          {isLoading ? "Generating..." : `Generate ${activeView} plan`}
        </Button>
        {currentPlan && (
          <Button variant="outline" size="sm" onClick={generate} disabled={isLoading}>
            Regenerate
          </Button>
        )}
      </div>

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-32 w-full" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Skeleton className="h-24 rounded-xl" />
            <Skeleton className="h-24 rounded-xl" />
          </div>
        </div>
      )}

      {!isLoading && currentPlan && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {currentPlan.context_summary && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(currentPlan.context_summary).map(([key, value]) => (
                <div key={key} className="rounded-lg bg-muted px-3 py-1.5 text-xs">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}: </span>
                  <span className="font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          )}

          <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap rounded-xl border bg-card p-6 text-sm leading-relaxed">
            {currentPlan.content}
          </div>

          <div className="flex items-center justify-between rounded-lg bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
            <span>Generated {new Date(currentPlan.generated_at).toLocaleString()}</span>
          </div>
        </motion.div>
      )}

      {!isLoading && !currentPlan && (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm text-muted-foreground">No plan generated yet</p>
          <Button onClick={generate}>Generate Plan</Button>
        </div>
      )}
    </div>
  );
}
