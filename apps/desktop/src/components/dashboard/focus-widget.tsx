import { Link } from "react-router-dom";

interface FocusWidgetProps {
  focusMinutes: number;
  date: string;
  xpEarned: number;
}

export function FocusWidget({ focusMinutes, date, xpEarned }: FocusWidgetProps) {
  const today = new Date(date).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-2 text-muted-foreground">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-xs font-medium">{today}</span>
      </div>
      <div className="mt-3 flex items-baseline gap-1">
        <span className="text-3xl font-bold">{focusMinutes}</span>
        <span className="text-sm text-muted-foreground">min focused</span>
      </div>
      {xpEarned > 0 && (
        <p className="mt-1 text-xs text-muted-foreground">+{xpEarned} XP earned today</p>
      )}
      <Link to="/pomodoro" className="mt-3 inline-flex items-center gap-1 text-xs text-primary hover:underline">
        Start a session
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
        </svg>
      </Link>
    </div>
  );
}
