import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent, Button, Skeleton } from "@fixly/ui";
import { getDashboard } from "@/lib/dashboard-service";

function formatGreeting(displayName: string): string {
  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  return `${timeGreeting}, ${displayName}`;
}

function todayDateString(): string {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: string;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg border bg-card p-4 shadow-sm transition-shadow hover:shadow-md ${color}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-bold">{value}</p>
        </div>
        <svg
          className="h-8 w-8 text-muted-foreground/30"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
        </svg>
      </div>
    </motion.div>
  );
}

function ProgressRing({ percentage, size = 80 }: { percentage: number; size?: number }) {
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        className="text-muted/20"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        className="text-primary"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-current text-lg font-bold"
      >
        {Math.round(percentage)}%
      </text>
    </svg>
  );
}

const priorityColors: Record<string, string> = {
  urgent: "text-red-500 bg-red-500/10",
  high: "text-orange-500 bg-orange-500/10",
  medium: "text-blue-500 bg-blue-500/10",
  low: "text-gray-500 bg-gray-500/10",
};

const statusColors: Record<string, string> = {
  pending: "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400",
  in_progress: "text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400",
  completed: "text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400",
  overdue: "text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400",
  cancelled: "text-gray-500 bg-gray-100 dark:bg-gray-800 dark:text-gray-400",
};

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-48" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Skeleton className="h-64 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) return <DashboardSkeleton />;
  if (!data) return null;

  const { profile, stats, recent_assignments, subjects } = data;
  const greeting = formatGreeting(profile.display_name);
  const dailyGoalHours = data.settings.daily_goal_hours || 0;
  const completedHoursToday = 0;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold">{greeting}</h1>
          <p className="text-sm text-muted-foreground">{todayDateString()}</p>
        </div>
        <div className="flex items-center gap-4">
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
        className="space-y-1"
      >
        <p className="text-sm text-muted-foreground">
          {stats.due_today > 0
            ? `${stats.due_today} assignment${stats.due_today !== 1 ? "s" : ""} due today`
            : "No assignments due today"}
          {stats.overdue > 0 && (
            <span className="ml-2 font-medium text-destructive">
              &middot; {stats.overdue} overdue
            </span>
          )}
          {stats.due_this_week > stats.due_today && (
            <span className="ml-2">
              &middot; {stats.due_this_week} due this week
            </span>
          )}
        </p>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Assignments"
          value={stats.total}
          color=""
          icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
        <StatCard
          label="In Progress"
          value={stats.in_progress}
          color="border-l-4 border-l-blue-500"
          icon="M13 10V3L4 14h7v7l9-11h-7z"
        />
        <StatCard
          label="Completed"
          value={stats.completed}
          color="border-l-4 border-l-green-500"
          icon="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
        <StatCard
          label="Overdue"
          value={stats.overdue}
          color={stats.overdue > 0 ? "border-l-4 border-l-red-500" : ""}
          icon="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base">Progress</CardTitle>
            <span className="text-xs text-muted-foreground">
              {stats.completed}/{stats.total} completed
            </span>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <ProgressRing percentage={stats.completion_percentage} size={100} />
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
                  <span>Pending: {stats.pending}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-yellow-500" />
                  <span>In Progress: {stats.in_progress}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
                  <span>Completed: {stats.completed}</span>
                </div>
                {stats.overdue > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                    <span>Overdue: {stats.overdue}</span>
                  </div>
                )}
                {dailyGoalHours > 0 && (
                  <div className="mt-3 border-t pt-2 text-muted-foreground">
                    Daily goal: {completedHoursToday}h / {dailyGoalHours}h
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base">Subjects</CardTitle>
            <Link to="/subjects">
              <Button variant="ghost" size="sm">Manage</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {subjects.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No subjects yet.{" "}
                <Link to="/subjects" className="text-primary underline-offset-4 hover:underline">
                  Add your first subject
                </Link>
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {subjects.map((subject) => (
                  <div
                    key={subject.id}
                    className="flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm"
                  >
                    <span
                      className="h-3 w-3 rounded-full shrink-0"
                      style={{ backgroundColor: subject.color || "#6366f1" }}
                    />
                    <span className="truncate">{subject.name}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Recent Assignments</CardTitle>
          <Link to="/assignments">
            <Button variant="ghost" size="sm">View all</Button>
          </Link>
        </CardHeader>
        <CardContent>
          {recent_assignments.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <svg className="h-12 w-12 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm text-muted-foreground">No assignments yet</p>
              <Link to="/assignments">
                <Button size="sm">+ Create Assignment</Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {recent_assignments.map((assignment) => {
                const subject = subjects.find((s) => s.id === assignment.subject_id);
                const isOverdue = assignment.status === "overdue";
                const isDueSoon =
                  assignment.due_date &&
                  !isOverdue &&
                  assignment.status !== "completed" &&
                  new Date(assignment.due_date).getTime() - Date.now() < 86400000 * 2;
                return (
                  <Link
                    key={assignment.id}
                    to={`/assignments/${assignment.id}`}
                    className="flex items-center gap-3 px-2 py-3 transition-colors hover:bg-muted/50 rounded-md -mx-2"
                  >
                    {subject?.color && (
                      <span
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: subject.color }}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-medium">{assignment.title}</p>
                        {assignment.is_pinned && (
                          <svg className="h-3 w-3 shrink-0 text-primary" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                          </svg>
                        )}
                      </div>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                        {assignment.due_date && (
                          <span className={isOverdue ? "text-destructive font-medium" : isDueSoon ? "text-orange-500 font-medium" : ""}>
                            Due {new Date(assignment.due_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[assignment.status] || statusColors.pending}`}>
                      {assignment.status.replace("_", " ")}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${priorityColors[assignment.priority] || priorityColors.medium}`}>
                      {assignment.priority}
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
