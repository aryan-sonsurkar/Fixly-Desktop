import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Button, Skeleton, Badge } from "@fixly/ui";
import { usePlannerStore } from "@/stores/planner-store";
import { usePomodoroStore } from "@/stores/pomodoro-store";
import {
  generateDailyPlan,
  generateWeeklyPlan,
  listPlans,
  parseScheduleItems,
  parsePlannerActions,
  synthesizeActionsFromSchedule,
  extractExplanation,
  executePlannerAction,
  formatPlanTime,
  planDayLabel,
  planDurationLabel,
  capitalizePlanWord,
  type PlanScheduleItem,
  type PlannerAction,
} from "@/lib/planner-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("planner-page");

function looksLikeJson(content: string): boolean {
  const s = content.trim();
  return s.startsWith("{") || s.startsWith("[") || s.startsWith("```");
}

function parseDateTime(iso: string): Date | null {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

const priorityDot: Record<string, string> = {
  low: "bg-muted-foreground",
  medium: "bg-blue-500",
  high: "bg-amber-500",
  urgent: "bg-red-500",
};

const priorityText: Record<string, string> = {
  low: "text-muted-foreground",
  medium: "text-blue-600 dark:text-blue-400",
  high: "text-amber-600 dark:text-amber-400",
  urgent: "text-red-600 dark:text-red-400",
};

const actionTypeMeta: Record<
  PlannerAction["action"],
  { label: string; badgeClass: string; actionBtnText: string; icon: string }
> = {
  create_study_session: {
    label: "Study Session",
    badgeClass: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20",
    actionBtnText: "Start Session",
    icon: "⏱",
  },
  create_task: {
    label: "Task",
    badgeClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
    actionBtnText: "Add Task",
    icon: "📋",
  },
  schedule_task: {
    label: "Schedule",
    badgeClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
    actionBtnText: "Schedule",
    icon: "📅",
  },
  reschedule_task: {
    label: "Reschedule",
    badgeClass: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
    actionBtnText: "Apply Reschedule",
    icon: "🔄",
  },
  prioritize_task: {
    label: "Priority Update",
    badgeClass: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
    actionBtnText: "Update Priority",
    icon: "⚡",
  },
};

function PlanTimeline({ items }: { items: PlanScheduleItem[] }) {
  const sorted = [...items].sort((a, b) => {
    const da = parseDateTime(a.start_time);
    const db = parseDateTime(b.start_time);
    if (!da && !db) return 0;
    if (!da) return 1;
    if (!db) return -1;
    return da.getTime() - db.getTime();
  });
  let lastDay = "";
  return (
    <div className="space-y-4">
      {sorted.map((item, i) => {
        const day = planDayLabel(item.start_time);
        const showDay = day !== "" && day !== lastDay;
        if (showDay) lastDay = day;
        const duration = planDurationLabel(item.start_time, item.end_time);
        return (
          <div key={i}>
            {showDay && (
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {day}
              </p>
            )}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3 rounded-xl border bg-card p-4 transition-shadow hover:shadow-sm"
            >
              <div className="w-32 shrink-0">
                <p className="text-sm font-semibold">
                  {formatPlanTime(item.start_time)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  – {formatPlanTime(item.end_time)}
                  {duration && <span> · {duration}</span>}
                </p>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">{item.title}</p>
                {item.description && (
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{item.description}</p>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <Badge variant="outline" className={priorityText[item.priority] || ""}>
                    <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${priorityDot[item.priority] || "bg-muted-foreground"}`} />
                    {capitalizePlanWord(item.priority)}
                  </Badge>
                  <Badge variant="secondary">{capitalizePlanWord(item.type)}</Badge>
                </div>
              </div>
            </motion.div>
          </div>
        );
      })}
    </div>
  );
}

function ActionCard({
  action,
  isExecuting,
  isExecuted,
  error,
  onExecute,
}: {
  action: PlannerAction;
  isExecuting: boolean;
  isExecuted: boolean;
  error?: string;
  onExecute: (action: PlannerAction) => void;
}) {
  const navigate = useNavigate();
  const meta = actionTypeMeta[action.action] || {
    label: action.action,
    badgeClass: "bg-muted text-muted-foreground",
    actionBtnText: "Execute",
    icon: "•",
  };

  const priority = ("priority" in action && action.priority ? action.priority : "medium") as keyof typeof priorityText;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col justify-between rounded-xl border p-4 transition-all ${
        isExecuted ? "border-emerald-500/30 bg-emerald-500/5" : "bg-card hover:border-primary/30"
      }`}
    >
      <div>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{meta.icon}</span>
            <Badge variant="outline" className={`text-xs ${meta.badgeClass}`}>
              {meta.label}
            </Badge>
          </div>
          <Badge variant="outline" className={`text-xs ${priorityText[priority] || ""}`}>
            <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${priorityDot[priority] || "bg-muted-foreground"}`} />
            {capitalizePlanWord(priority)}
          </Badge>
        </div>

        <h4 className="mt-2.5 text-sm font-semibold tracking-tight">{action.title}</h4>

        {"description" in action && action.description && (
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground line-clamp-2">
            {action.description}
          </p>
        )}

        {action.action === "create_study_session" && (
          <div className="mt-2 text-xs text-muted-foreground">
            <span>Duration: {action.duration_minutes} min</span>
            {action.scheduled_time && (
              <span className="ml-2">· {formatPlanTime(action.scheduled_time)}</span>
            )}
          </div>
        )}

        {action.action === "schedule_task" && (
          <div className="mt-2 text-xs text-muted-foreground">
            {formatPlanTime(action.start_time)} – {formatPlanTime(action.end_time)}
            {" · "}
            <span className="capitalize">{action.type}</span>
          </div>
        )}

        {action.action === "reschedule_task" && (
          <div className="mt-2 text-xs text-muted-foreground">
            <span>New time: {formatPlanTime(action.new_start_time)}</span>
            {action.reason && <span> · {action.reason}</span>}
          </div>
        )}

        {action.action === "prioritize_task" && action.reason && (
          <p className="mt-1 text-xs text-muted-foreground">{action.reason}</p>
        )}
      </div>

      <div className="mt-4 pt-2 border-t flex flex-wrap items-center justify-between gap-2">
        {error && (
          <span className="text-xs text-destructive truncate max-w-[200px]" title={error}>
            {error}
          </span>
        )}

        <div className="flex items-center gap-2 ml-auto">
          {isExecuted ? (
            <>
              <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 py-1 px-2.5">
                ✓ {action.action === "create_study_session" ? "Ready" : "Added"}
              </Badge>
              {action.action === "create_study_session" && (
                <Button size="sm" variant="outline" onClick={() => navigate("/pomodoro")}>
                  Open Timer
                </Button>
              )}
            </>
          ) : (
            <Button
              size="sm"
              variant="default"
              disabled={isExecuting}
              onClick={() => onExecute(action)}
            >
              {isExecuting ? "Executing..." : meta.actionBtnText}
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function PlannerPage() {
  const {
    dailyPlan, weeklyPlan,
    loadingDaily, loadingWeekly,
    activeView, setActiveView, error, setError,
    setDailyPlan, setWeeklyPlan,
    setLoadingDaily, setLoadingWeekly,
  } = usePlannerStore();

  const [executingActions, setExecutingActions] = useState<Record<string, boolean>>({});
  const [executedActions, setExecutedActions] = useState<Record<string, boolean>>({});
  const [actionErrors, setActionErrors] = useState<Record<string, string>>({});

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

  const currentPlan = activeView === "daily" ? dailyPlan : weeklyPlan;
  const isLoading = activeView === "daily" ? loadingDaily : loadingWeekly;

  // Restore executed state for current plan from localStorage
  useEffect(() => {
    if (!currentPlan) return;
    try {
      const key = `fixly:executed_actions:${currentPlan.conversation_id || "default"}`;
      const saved = localStorage.getItem(key);
      if (saved) {
        setExecutedActions(JSON.parse(saved));
      } else {
        setExecutedActions({});
      }
    } catch {
      // ignore
    }
  }, [currentPlan?.conversation_id]);

  const saveExecutedAction = (actionId: string) => {
    setExecutedActions((prev) => {
      const updated = { ...prev, [actionId]: true };
      if (currentPlan?.conversation_id) {
        try {
          const key = `fixly:executed_actions:${currentPlan.conversation_id}`;
          localStorage.setItem(key, JSON.stringify(updated));
        } catch {
          // ignore
        }
      }
      return updated;
    });
  };

  const handleExecuteAction = async (action: PlannerAction) => {
    const aid = action.action_id;
    if (executingActions[aid] || executedActions[aid]) return;

    setExecutingActions((prev) => ({ ...prev, [aid]: true }));
    setActionErrors((prev) => {
      const copy = { ...prev };
      delete copy[aid];
      return copy;
    });

    try {
      await executePlannerAction(action);
      saveExecutedAction(aid);

      // If study session, configure Pomodoro store
      if (action.action === "create_study_session") {
        const mins = action.duration_minutes || 25;
        usePomodoroStore.getState().setTotalTime(mins * 60);
        usePomodoroStore.getState().setTimeRemaining(mins * 60);
        usePomodoroStore.getState().setPhase("focus");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Execution failed";
      setActionErrors((prev) => ({ ...prev, [aid]: msg }));
      logger.error("Failed to execute action", err);
    } finally {
      setExecutingActions((prev) => ({ ...prev, [aid]: false }));
    }
  };

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
        const r = err as { response?: { data?: { detail?: string; error?: string } }; message?: string };
        // Backend serializes FixlyError as { error, code, status }.
        if (r.response?.data?.detail) return r.response.data.detail;
        if (r.response?.data?.error) return r.response.data.error;
        if (r.message) return r.message;
      }
      return err instanceof Error ? err.message : "Failed to generate plan";
    };

    if (activeView === "daily") {
      setLoadingDaily(true);
      try {
        const p = await withTimeout(generateDailyPlan(), 300_000);
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
        const p = await withTimeout(generateWeeklyPlan(), 300_000);
        setWeeklyPlan(p);
      } catch (err) {
        setError(getErrMsg(err));
        logger.error("Failed to generate plan", err);
      } finally {
        setLoadingWeekly(false);
      }
    }
  };

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Study Planner</h1>
          <p className="text-sm text-muted-foreground">AI-powered study plans tailored to your workload</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex gap-1 rounded-lg border bg-muted/50 p-1">
            {(["daily", "weekly"] as const).map((view) => (
              <button
                key={view}
                type="button"
                onClick={() => setActiveView(view)}
                className={`rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors capitalize ${
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
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
          <span className="flex-1">{error}</span>
          <button type="button" onClick={() => setError(null)} className="rounded p-0.5 hover:bg-destructive/20">✕</button>
        </div>
      )}

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {!isLoading && currentPlan && (() => {
        // Derive schedule timeline items
        const timelineItems = currentPlan.schedule_items?.length
          ? currentPlan.schedule_items
          : parseScheduleItems(currentPlan.content);

        // Derive structured actions
        let actions = currentPlan.actions?.length
          ? currentPlan.actions
          : parsePlannerActions(currentPlan.content);

        if (actions.length === 0 && timelineItems.length > 0) {
          actions = synthesizeActionsFromSchedule(timelineItems);
        }

        // Derive natural-language explanation
        const explanation =
          currentPlan.explanation && currentPlan.explanation.trim()
            ? currentPlan.explanation.trim()
            : extractExplanation(currentPlan.content);

        const hasUsableStructure = actions.length > 0 || timelineItems.length > 0;

        if (!hasUsableStructure) {
          if (looksLikeJson(currentPlan.content)) {
            return (
              <div className="flex items-center justify-between gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm">
                <span className="text-destructive">Fixly couldn&apos;t structure that plan. Please try again.</span>
                <Button size="sm" variant="outline" onClick={() => void generate()}>
                  Retry
                </Button>
              </div>
            );
          }
          return (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap rounded-xl border bg-card p-6 text-sm leading-relaxed"
            >
              {currentPlan.content}
            </motion.div>
          );
        }

        return (
          <div className="space-y-6">
            {/* Planner Explanation: Clearly separated from actions */}
            {explanation && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border bg-muted/40 p-5 leading-relaxed"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                    ✦
                  </span>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Fixly Plan Strategy
                  </h3>
                </div>
                <p className="text-sm leading-relaxed">{explanation}</p>
              </motion.div>
            )}

            {/* Proposed Structured Actions */}
            {actions.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Proposed Actions ({actions.length})
                  </h3>
                  <span className="text-xs text-muted-foreground">One-click add to your schedule</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {actions.map((act) => (
                    <ActionCard
                      key={act.action_id}
                      action={act}
                      isExecuting={Boolean(executingActions[act.action_id])}
                      isExecuted={Boolean(executedActions[act.action_id])}
                      error={actionErrors[act.action_id]}
                      onExecute={handleExecuteAction}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Timeline Schedule */}
            {timelineItems.length > 0 && (
              <div className="space-y-3 pt-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Schedule Timeline
                </h3>
                <PlanTimeline items={timelineItems} />
              </div>
            )}
          </div>
        );
      })()}

      {!isLoading && !currentPlan && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-sm text-muted-foreground">No plan yet. Click Generate to start.</p>
        </div>
      )}
    </div>
  );
}
