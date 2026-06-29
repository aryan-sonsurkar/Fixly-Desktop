import { useEffect, useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Skeleton } from "@fixly/ui";
import { getDashboard } from "@/lib/dashboard-service";
import { getStudyStatistics } from "@/lib/study-service";
import { generateDailyPlan } from "@/lib/planner-service";
import { getDailyMission, assessRisk } from "@/lib/copilot-service";
import { useDashboardStore } from "@/stores/dashboard-store";
import { useSearchStore } from "@/stores/search-store";
import { BriefingWidget } from "@/components/dashboard/briefing-widget";
import { FocusWidget } from "@/components/dashboard/focus-widget";
import { DeadlinesWidget } from "@/components/dashboard/deadlines-widget";
import { QuickActionsWidget } from "@/components/dashboard/quick-actions-widget";
import { XPStreakWidget, ProductivityScoreWidget } from "@/components/dashboard/xp-streak-widget";
import { EmailWidget } from "@/components/dashboard/email-widget";
import { MissionWidget } from "@/components/dashboard/mission-widget";
import { HealthWidget } from "@/components/dashboard/health-widget";
import { MomentumWidget } from "@/components/dashboard/momentum-widget";
import { RiskAlertsWidget } from "@/components/dashboard/risk-alerts-widget";

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
    widgets,
    mission, missionLoading, setMission, setMissionLoading,
    risk, riskLoading, setRisk, setRiskLoading,
  } = useDashboardStore();
  const { setOpen: setSearchOpen } = useSearchStore();
  const dragItem = useRef<number | null>(null);
  const [orderedWidgets, setOrderedWidgets] = useState(
    widgets.filter((w) => w.visible).sort((a, b) => a.order - b.order),
  );

  const { data: rawData, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  const { data: studyStats } = useQuery({
    queryKey: ["study-statistics"],
    queryFn: getStudyStatistics,
  });

  useEffect(() => {
    if (rawData) {
      setData(rawData);
      setLoading(false);
    }
  }, [rawData, setData, setLoading]);

  useEffect(() => {
    setOrderedWidgets(widgets.filter((w) => w.visible).sort((a, b) => a.order - b.order));
  }, [widgets]);

  const handleGenerateBriefing = useCallback(async () => {
    setBriefingLoading(true);
    try {
      const plan = await generateDailyPlan();
      setBriefing(plan);
    } catch {
      // silently fail
    } finally {
      setBriefingLoading(false);
    }
  }, [setBriefing, setBriefingLoading]);

  const handleGenerateMission = useCallback(async () => {
    setMissionLoading(true);
    try {
      const result = await getDailyMission();
      setMission(result);
    } catch {
      // silently fail
    } finally {
      setMissionLoading(false);
    }
  }, [setMission, setMissionLoading]);

  const handleRefreshRisk = useCallback(async () => {
    setRiskLoading(true);
    try {
      const result = await assessRisk();
      setRisk(result);
    } catch {
      // silently fail
    } finally {
      setRiskLoading(false);
    }
  }, [setRisk, setRiskLoading]);

  const handleDragStart = (index: number) => {
    dragItem.current = index;
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (dragItem.current === null || dragItem.current === index) return;
    const items = [...orderedWidgets];
    const [moved] = items.splice(dragItem.current, 1);
    items.splice(index, 0, moved);
    dragItem.current = index;
    setOrderedWidgets(items);
  };

  const handleDragEnd = () => {
    dragItem.current = null;
  };

  if (isLoading || loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 rounded-xl" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      </div>
    );
  }

  const profile = data?.profile || { display_name: "Student", xp: 0, streak: 0 };
  const stats = data?.stats || {
    total: 0, completed: 0, pending: 0, in_progress: 0,
    overdue: 0, due_today: 0, due_this_week: 0, completion_percentage: 0,
  };
  const recentAssignments = data?.recent_assignments || [];

  // Parse risk alerts from the AI response
  const parsedAlerts = (() => {
    if (!risk?.content) return [];
    try {
      const jsonMatch = risk.content.match(/\{[\s\S]*"alerts"[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.alerts || [];
      }
    } catch {
      // fallback
    }
    return [];
  })();

  const widgetComponents: Record<string, React.ReactNode> = {
    briefing: (
      <BriefingWidget
        briefing={briefing}
        loading={briefingLoading}
        onGenerate={handleGenerateBriefing}
      />
    ),
    mission: (
      <MissionWidget
        mission={mission}
        loading={missionLoading}
        onGenerate={handleGenerateMission}
      />
    ),
    health: (
      <HealthWidget
        score={risk?.academic_health_score ?? 50}
        riskLevel={risk?.risk_level ?? "Low"}
        loading={riskLoading}
        onRefresh={handleRefreshRisk}
      />
    ),
    risk_alerts: (
      <RiskAlertsWidget
        alerts={parsedAlerts}
        loading={riskLoading}
        onRefresh={handleRefreshRisk}
      />
    ),
    momentum: (
      <MomentumWidget
        streak={profile.streak}
        weeklyHours={studyStats?.total_study_hours ?? 0}
        weeklyCycles={0}
        studyDays={studyStats?.total_study_days ?? 0}
        loading={false}
      />
    ),
    focus: (
      <FocusWidget
        focusMinutes={stats.total || 0}
        date={new Date().toISOString()}
        xpEarned={studyStats?.total_study_points || 0}
      />
    ),
    tasks: (
      <div className="rounded-xl border bg-card p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold">AI Recommended Tasks</h3>
        <div className="space-y-2 text-sm">
          {stats.pending > 0 ? (
            [
              { label: `${stats.pending} pending assignments`, color: "text-yellow-500" },
              ...(stats.overdue > 0
                ? [{ label: `${stats.overdue} overdue`, color: "text-red-500" as const }]
                : []),
            ].map((t) => (
              <div key={t.label} className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2">
                <span className={`h-2 w-2 rounded-full ${t.color}`} />
                <span className="text-muted-foreground">{t.label}</span>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">All caught up! No pending tasks.</p>
          )}
        </div>
      </div>
    ),
    assignments: (
      <DeadlinesWidget
        deadlines={recentAssignments.map((a: any) => ({
          title: a.title,
          due: a.due_date || new Date().toISOString(),
          priority: a.priority || "medium",
          status: a.status,
        }))}
        total={stats.total}
        urgent={stats.overdue}
      />
    ),
    emails: <EmailWidget unread={0} pendingReview={0} />,
    xp: <XPStreakWidget xp={profile.xp} streak={profile.streak} />,
    score: <ProductivityScoreWidget score={stats.completion_percentage} />,
    actions: <QuickActionsWidget onOpenSearch={() => setSearchOpen(true)} />,
    pomodoro: (
      <div className="rounded-xl border bg-card p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold">Pomodoro</h3>
        <p className="text-sm text-muted-foreground">No active session.</p>
      </div>
    ),
  };

  const topRowTypes = ["health", "momentum", "risk_alerts", "focus", "xp", "score", "pomodoro"];
  const midRowTypes = ["mission", "briefing"];
  const bottomRowTypes = ["assignments", "tasks", "actions", "emails"];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold">{formatGreeting(profile.display_name)}</h1>
          <p className="text-sm text-muted-foreground">{todayString()}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-1.5">
            <svg className="h-4 w-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <span className="text-sm font-semibold">{profile.xp} XP</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-1.5">
            <svg className="h-4 w-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            </svg>
            <span className="text-sm font-semibold">{profile.streak} day streak</span>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <p className="text-sm text-muted-foreground">
          {stats.due_today > 0
            ? `${stats.due_today} assignment${stats.due_today !== 1 ? "s" : ""} due today`
            : "No assignments due today"}
          {stats.overdue > 0 && (
            <span className="ml-2 font-medium text-destructive">&middot; {stats.overdue} overdue</span>
          )}
          {stats.due_this_week > stats.due_today && (
            <span className="ml-2">&middot; {stats.due_this_week} due this week</span>
          )}
        </p>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {orderedWidgets
          .filter((w) => topRowTypes.includes(w.type))
          .map((widget) => (
            <motion.div
              key={widget.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              draggable
              onDragStart={() => handleDragStart(orderedWidgets.indexOf(widget))}
              onDragOver={(e) => handleDragOver(e, orderedWidgets.indexOf(widget))}
              onDragEnd={handleDragEnd}
              className="cursor-grab active:cursor-grabbing"
            >
              {widgetComponents[widget.type]}
            </motion.div>
          ))}
      </div>

      {orderedWidgets
        .filter((w) => midRowTypes.includes(w.type))
        .map((widget) => (
          <motion.div
            key={widget.id}
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {widgetComponents[widget.type]}
          </motion.div>
        ))}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {orderedWidgets
          .filter((w) => bottomRowTypes.includes(w.type))
          .map((widget) => (
            <motion.div
              key={widget.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              draggable
              onDragStart={() => handleDragStart(orderedWidgets.indexOf(widget))}
              onDragOver={(e) => handleDragOver(e, orderedWidgets.indexOf(widget))}
              onDragEnd={handleDragEnd}
              className="cursor-grab active:cursor-grabbing"
            >
              {widgetComponents[widget.type]}
            </motion.div>
          ))}
      </div>
    </div>
  );
}
