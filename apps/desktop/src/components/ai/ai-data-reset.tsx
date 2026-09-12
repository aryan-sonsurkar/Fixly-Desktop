import { useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle, CardDescription } from "@fixly/ui";
import { resetAllMemories } from "@/lib/memory-service";

export function AIDataResetSection() {
  const [confirming, setConfirming] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [done, setDone] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    try {
      await resetAllMemories();
      setDone(true);
      setConfirming(false);
    } catch {
      // silently fail
    } finally {
      setResetting(false);
    }
  };

  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-destructive">
          Reset AI Data
        </CardTitle>
        <CardDescription>
          Delete all AI memories, conversation history, and learned preferences.
          This cannot be undone.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {done ? (
          <p className="text-sm text-green-600 dark:text-green-400">
            All AI data has been reset. Fixly has no remaining memories about you.
          </p>
        ) : confirming ? (
          <div className="space-y-3">
            <p className="text-sm text-destructive font-medium">
              Are you absolutely sure? This permanently deletes:
            </p>
            <ul className="text-xs text-muted-foreground space-y-1 ml-4">
              <li>• All stored memories and learned preferences</li>
              <li>• Conversation history and summaries</li>
              <li>• Academic profile data</li>
              <li>• Goals, skills, and roadmaps</li>
            </ul>
            <div className="flex gap-2">
              <Button
                variant="destructive"
                size="sm"
                onClick={handleReset}
                disabled={resetting}
              >
                {resetting ? "Resetting..." : "Yes, reset everything"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirming(false)}
                disabled={resetting}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setConfirming(true)}
          >
            Reset All AI Data
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
