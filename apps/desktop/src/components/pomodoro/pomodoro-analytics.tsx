import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@fixly/ui";
import { motion } from "framer-motion";
import type { PomodoroAnalyticsData } from "@/lib/pomodoro-service";

interface PomodoroAnalyticsProps {
  open: boolean;
  analytics: PomodoroAnalyticsData | null;
  onClose: () => void;
}

function StatCard({ label, value, suffix = "" }: { label: string; value: string | number; suffix?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border bg-card p-3 text-center"
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-bold">
        {value}{suffix}
      </p>
    </motion.div>
  );
}

export function PomodoroAnalytics({ open, analytics, onClose }: PomodoroAnalyticsProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Pomodoro Analytics</DialogTitle>
        </DialogHeader>
        {!analytics ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Loading...</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <StatCard label="Total Sessions" value={analytics.total_sessions} />
              <StatCard label="Focus Minutes" value={analytics.total_focus_minutes} />
              <StatCard label="Total Cycles" value={analytics.total_cycles} />
              <StatCard label="Avg Focus" value={analytics.average_focus_minutes} suffix="m" />
              <StatCard label="Current Streak" value={analytics.current_streak} suffix="d" />
              <StatCard label="Best Streak" value={analytics.longest_streak} suffix="d" />
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">Daily Goal Progress</p>
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${analytics.daily_goal_progress * 100}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              </div>
              <p className="mt-1 text-right text-xs text-muted-foreground">
                {Math.round(analytics.daily_goal_progress * 100)}% of daily goal
              </p>
            </div>

            {analytics.weekly_data.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">This Week</p>
                <div className="flex items-end gap-1">
                  {analytics.weekly_data.slice(-7).map((d) => {
                    const max = Math.max(...analytics.weekly_data.map((w) => w.minutes), 1);
                    const h = (d.minutes / max) * 80;
                    return (
                      <div key={d.date} className="flex flex-1 flex-col items-center gap-1">
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: h }}
                          transition={{ duration: 0.5 }}
                          className="w-full rounded-sm bg-primary/60"
                          style={{ height: Math.max(h, 4) }}
                        />
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(d.date).toLocaleDateString("en", { weekday: "short" }).charAt(0)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
