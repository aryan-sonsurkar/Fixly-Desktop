import { useEffect } from "react";
import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";
import { usePlannerStore } from "@/stores/planner-store";
import { generateDailyPlan, generateWeeklyPlan, listPlans } from "@/lib/planner-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("planner-page");

export function PlannerPage() {
  const {
    dailyPlan, weeklyPlan,
    loadingDaily, loadingWeekly,
    activeView, setActiveView, error, setError,
    setDailyPlan, setWeeklyPlan,
    setLoadingDaily, setLoadingWeekly,
  } = usePlannerStore();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const plans = await listPlans();
        if (cancelled) return;
        const daily = plans.find((p) => p.plan_type === "daily");
        const weekly = plans.find((p) => p.plan_type === "weekly");
        if (daily) setDailyPlan(daily);
        if (weekly) setWeeklyPlan(weekly);
      } catch {
        logger.warn("Failed to load existing plans");
      }
    })();
    return () => { cancelled = true; };
  }, [setDailyPlan, setWeeklyPlan]);

  const generate = async () => {
    setError(null);
    const withTimeout = async <T,>(promise: Promise<T>, ms: number): Promise<T> => {
      let tid: ReturnType<typeof setTimeout>;
      const timeout = new Promise<never>((_, rej) => {
        tid = setTimeout(() => rej(new Error("Plan generation timed out — AI took too long. Please try again.")), ms);
      });
      try {
        return await Promise.race([promise, timeout]);
      } finally {
        clearTimeout(tid!);
      }
    };
    const getErrMsg = (err: unknown): string => {
      if (err && typeof err === "object" && "response" in err) {
        const r = err as { response?: { data?: { detail?: string } }; message?: string };
        if (r.response?.data?.detail) return r.response.data.detail;
        if (r.message) return r.message;
      }
      return err instanceof Error ? err.message : "Failed to generate plan";
    };
    if (activeView === "daily") {
      setLoadingDaily(true);
      try {
        const p = await withTimeout(generateDailyPlan(), 90_000);
        setDailyPlan(p);
      } catch (err) {
        setError(getErrMsg(err));
        logger.error("Failed to generate plan", err);
      } finally {
        setLoadingDaily(false);
      }
    } else {
      setLoadingWeekly(true);
      try {
        const p = await withTimeout(generateWeeklyPlan(), 90_000);
        setWeeklyPlan(p);
      } catch (err) {
        setError(getErrMsg(err));
        logger.error("Failed to generate plan", err);
      } finally {
        setLoadingWeekly(false);
      }
    }
  };

  const currentPlan = activeView === "daily" ? dailyPlan : weeklyPlan;
  const isLoading = activeView === "daily" ? loadingDaily : loadingWeekly;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Study Planner</h1>
        <p className="text-sm text-muted-foreground">AI-powered study plans tailored to your workload</p>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
          <span className="flex-1">{error}</span>
          <button type="button" onClick={() => setError(null)} className="rounded p-0.5 hover:bg-destructive/20">✕</button>
        </div>
      )}

      <div className="mb-6 flex items-center gap-3">
        <div className="flex gap-1 rounded-lg border bg-muted/50 p-1">
          {(["daily", "weekly"] as const).map((view) => (
            <button
              key={view}
              type="button"
              onClick={() => setActiveView(view)}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors capitalize ${
                activeView === view ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {view}
            </button>
          ))}
        </div>
        <Button onClick={generate} disabled={isLoading} size="sm">
          {isLoading ? "Generating..." : currentPlan ? "Regenerate" : "Generate"}
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {!isLoading && currentPlan && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap rounded-xl border bg-card p-6 text-sm leading-relaxed"
        >
          {currentPlan.content}
        </motion.div>
      )}

      {!isLoading && !currentPlan && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-sm text-muted-foreground">No plan yet. Click Generate to start.</p>
        </div>
      )}
    </div>
  );
}
