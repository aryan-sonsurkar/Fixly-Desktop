import { Badge } from "@fixly/ui";

export interface WorkflowStepUI {
  id: string;
  label: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
}

interface WorkflowActivityProps {
  name: string;
  steps: WorkflowStepUI[];
  status: string;
  onCancel?: () => void;
}

const STATUS_ICON: Record<string, string> = {
  pending: "○",
  running: "⏳",
  completed: "✓",
  failed: "✗",
  skipped: "–",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-muted-foreground",
  running: "text-amber-500",
  completed: "text-green-500",
  failed: "text-destructive",
  skipped: "text-muted-foreground",
};

export function WorkflowActivity({
  name,
  steps,
  status,
  onCancel,
}: WorkflowActivityProps) {
  const completedCount = steps.filter((s) => s.status === "completed").length;
  const total = steps.length;

  return (
    <div className="border rounded-lg p-3 bg-muted/30 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{name}</p>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px]">
            {completedCount}/{total}
          </Badge>
          {status === "running" && onCancel && (
            <button
              onClick={onCancel}
              className="text-xs text-muted-foreground hover:text-destructive transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="space-y-1">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-2 text-xs">
            <span className={STATUS_COLOR[step.status]}>
              {STATUS_ICON[step.status]}
            </span>
            <span
              className={
                step.status === "completed"
                  ? "text-muted-foreground"
                  : step.status === "running"
                    ? "text-foreground font-medium"
                    : "text-muted-foreground"
              }
            >
              {step.label}
            </span>
            {step.status === "running" && (
              <span className="text-amber-500 animate-pulse text-[10px]">
                working...
              </span>
            )}
          </div>
        ))}
      </div>

      {status === "completed" && (
        <p className="text-xs text-green-600 dark:text-green-400">
          Workflow completed successfully.
        </p>
      )}
      {status === "failed" && (
        <p className="text-xs text-destructive">
          Workflow failed. Some steps may not have completed.
        </p>
      )}
    </div>
  );
}
