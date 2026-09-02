import { useUpdater } from "@/hooks/useUpdater";
import { Button } from "@fixly/ui";

export function UpdaterBanner() {
  const { state, downloadAndInstall, dismiss, retry } = useUpdater();

  if (state.status === "idle" || state.status === "checking" || state.status === "up_to_date" || state.status === "deferred") {
    return null;
  }

  if (state.status === "downloading") {
    const pct = state.total ? Math.round((state.downloaded / state.total) * 100) : null;
    return (
      <div className="flex items-center justify-between gap-3 border-b bg-primary/5 px-4 py-2 text-sm">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
          Downloading update{pct !== null ? ` ${pct}%` : "..."}
        </span>
        <span className="text-xs text-muted-foreground">{state.total ? `${(state.downloaded / 1024 / 1024).toFixed(1)} MB` : ""}</span>
      </div>
    );
  }

  if (state.status === "ready_to_restart") {
    return (
      <div className="flex items-center justify-between gap-3 border-b bg-green-500/10 px-4 py-2 text-sm">
        <span className="text-green-700 dark:text-green-300">
          Update {state.version} downloaded — restart Fixly to apply.
        </span>
        <Button size="sm" onClick={() => window.location.reload()}>
          Restart now
        </Button>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="flex items-center justify-between gap-3 border-b bg-destructive/10 px-4 py-2 text-sm">
        <span className="text-destructive">Update check failed. Will retry next launch.</span>
        <div className="flex gap-2">
          <button type="button" onClick={retry} className="text-xs text-destructive underline hover:no-underline">
            Retry
          </button>
          <button type="button" onClick={dismiss} className="text-xs text-muted-foreground underline hover:no-underline">
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  // available
  if (state.status === "available") {
    return (
      <div className="flex items-center justify-between gap-3 border-b bg-card px-4 py-2.5 text-sm shadow-sm">
        <span>
          <span className="font-medium">Fixly {state.version} is available.</span>
          <span className="ml-2 text-muted-foreground hidden sm:inline">Update without losing your data.</span>
        </span>
        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" onClick={downloadAndInstall}>
            Update now
          </Button>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent"
          >
            Later
          </button>
        </div>
      </div>
    );
  }

  return null;
}
