import { useState, useEffect, useCallback } from "react";
import { Button, Badge, Card, CardContent, CardHeader, CardTitle } from "@fixly/ui";
import { getNudges, dismissNudge, type Nudge } from "@/lib/proactive-service";

const PRIORITY_COLOR: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

const TYPE_ICON: Record<string, string> = {
  deadline_reminder: "📅",
  study_suggestion: "📚",
  weakness_alert: "⚡",
  goal_progress: "🎯",
};

export function ProactiveInsights() {
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getNudges();
      setNudges(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDismiss = async (id: string) => {
    await dismissNudge(id);
    setNudges((prev) => prev.filter((n) => n.id !== id));
  };

  if (loading || nudges.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          AI Insights
          <Badge variant="secondary" className="text-[10px]">
            {nudges.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {nudges.slice(0, 3).map((nudge) => (
          <div
            key={nudge.id}
            className={`border-l-2 pl-3 py-1.5 ${PRIORITY_COLOR[nudge.priority] || "border-l-muted"}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium flex items-center gap-1">
                  <span>{TYPE_ICON[nudge.type] || "💡"}</span>
                  {nudge.title}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                  {nudge.message}
                </p>
              </div>
              <button
                onClick={() => handleDismiss(nudge.id)}
                className="text-muted-foreground hover:text-foreground shrink-0"
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            {nudge.action_suggestion && (
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-[10px] mt-1 px-2"
              >
                {nudge.action_suggestion}
              </Button>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
