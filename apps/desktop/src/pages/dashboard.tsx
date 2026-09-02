import { useEffect, useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "@fixly/ui";
import { getDashboard } from "@/lib/dashboard-service";
import { generateDailyPlan } from "@/lib/planner-service";
import { useDashboardStore } from "@/stores/dashboard-store";
import { useSearchStore } from "@/stores/search-store";
import { BriefingWidget } from "@/components/dashboard/briefing-widget";
import { FocusWidget } from "@/components/dashboard/focus-widget";
import { DeadlinesWidget } from "@/components/dashboard/deadlines-widget";
import { QuickActionsWidget } from "@/components/dashboard/quick-actions-widget";

function formatGreeting(name: string): string {
  const h = new Date().getHours();
  return `${h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"}, ${name}`;
}

function todayString(): string {
  return new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

export function DashboardPage() {
  const {
    data, setData, loading, setLoading,
    briefing, setBriefing, briefingLoading, setBriefingLoading,
  } = useDashboardStore();
  const { setOpen: setSearchOpen } = useSearchStore();
  const mountedRef = useRef(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const { data: rawData, isLoading: queryLoading, isError, error: queryError, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    retry: 1,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    placeholderData: (prev) => prev,
  });

  useEffect(() => {
    if (isError) {
      const msg = queryError instanceof Error ? queryError.message : "Failed to load dashboard";
      setError(msg);
      setLoading(false);
      return;
    }
    if (rawData) {
      setData(rawData);
      setLoading(false);
      setError(null);
    }
  }, [rawData, isError, queryError, setData, setLoading]);

  const handleGenerateBriefing = useCallback(async () => {
    setBriefingLoading(true);
    try {
      const plan = await generateDailyPlan();
      if (mountedRef.current) setBriefing(plan);
    } catch {
      // silent
    } finally {
      if (mountedRef.current) setBriefingLoading(false);
    }
  }, [setBriefing, setBriefingLoading]);

  if (isError && !rawData) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <h2 className="text-lg font-semibold">Failed to load dashboard</h2>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const showSkeleton = (queryLoading || loading) && !rawData && !data;
  if (showSkeleton) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      </div>
    );
  }

  const profile = data?.profile || { display_name: "Student" };
  const stats = data?.stats || {
    total: 0, completed: 0, pending: 0, in_progress: 0,
    overdue: 0, due_today: 0, due_this_week: 0, completion_percentage: 0,
  };
  const recentAssignments = data?.recent_assignments || [];

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">{formatGreeting(profile.display_name)}</h1>
        <p className="text-sm text-muted-foreground">{todayString()}</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {stats.due_today > 0
            ? `${stats.due_today} assignment${stats.due_today !== 1 ? "s" : ""} due today`
            : "No assignments due today"}
          {stats.overdue > 0 && (
            <span className="ml-2 font-medium text-destructive">&middot; {stats.overdue} overdue</span>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FocusWidget
          focusMinutes={data?.study?.total_hours ? Math.round(data.study.total_hours * 60) : 0}
          date={new Date().toISOString()}
          xpEarned={data?.today?.xp_earned ?? 0}
        />
        <BriefingWidget
          briefing={briefing}
          loading={briefingLoading}
          onGenerate={handleGenerateBriefing}
        />
        <DeadlinesWidget
          deadlines={recentAssignments.map((a: unknown) => {
            const r = a as Record<string, unknown>;
            return {
              title: (r.title as string) || "",
              due: (r.due as string) || (r.due_date as string) || new Date().toISOString(),
              priority: (r.priority as string) || "medium",
              status: r.status as string,
            };
          })}
          total={stats.total}
          urgent={stats.overdue}
        />
        <QuickActionsWidget onOpenSearch={() => setSearchOpen(true)} />
      </div>
    </div>
  );
}
