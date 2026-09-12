import { Button, Badge } from "@fixly/ui";

export interface ActionRequest {
  id: string;
  tool_name: string;
  description: string;
  parameters: Record<string, unknown>;
  requires_confirmation: boolean;
  confirmation_message?: string;
  status: "pending" | "executing" | "completed" | "failed" | "cancelled";
  result?: unknown;
  error?: string;
}

interface ActionConfirmationProps {
  action: ActionRequest;
  onConfirm: (id: string) => void;
  onCancel: (id: string) => void;
}

export function ActionConfirmation({
  action,
  onConfirm,
  onCancel,
}: ActionConfirmationProps) {
  if (action.status === "completed") {
    return (
      <div className="flex items-start gap-2 text-sm py-1">
        <span className="text-green-500 mt-0.5">✓</span>
        <span className="text-muted-foreground">{action.description}</span>
      </div>
    );
  }

  if (action.status === "failed") {
    return (
      <div className="flex items-start gap-2 text-sm py-1">
        <span className="text-destructive mt-0.5">✗</span>
        <span className="text-muted-foreground">
          {action.description}
          {action.error && (
            <span className="text-destructive ml-1">— {action.error}</span>
          )}
        </span>
      </div>
    );
  }

  if (action.status === "cancelled") {
    return (
      <div className="flex items-start gap-2 text-sm py-1">
        <span className="text-muted-foreground mt-0.5">○</span>
        <span className="text-muted-foreground line-through">
          {action.description}
        </span>
        <Badge variant="outline" className="text-[10px]">
          Cancelled
        </Badge>
      </div>
    );
  }

  if (action.status === "executing") {
    return (
      <div className="flex items-start gap-2 text-sm py-1">
        <span className="text-amber-500 mt-0.5 animate-pulse">⏳</span>
        <span className="text-muted-foreground">{action.description}</span>
      </div>
    );
  }

  // pending - needs confirmation
  if (action.requires_confirmation) {
    return (
      <div className="border rounded-lg p-3 bg-muted/50 space-y-2">
        <p className="text-sm font-medium">Fixly AI wants to:</p>
        <p className="text-sm text-muted-foreground">{action.description}</p>
        {action.confirmation_message && (
          <p className="text-xs text-muted-foreground italic">
            {action.confirmation_message}
          </p>
        )}
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onCancel(action.id)}
          >
            Cancel
          </Button>
          <Button size="sm" onClick={() => onConfirm(action.id)}>
            Confirm
          </Button>
        </div>
      </div>
    );
  }

  // pending - safe action, auto-execute
  return null;
}
