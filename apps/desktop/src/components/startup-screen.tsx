import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";

interface StartupStatus {
  stage: string;
  message: string;
  error?: string | null;
  port?: number | null;
  pid?: number | null;
}

const STAGES: Record<string, { label: string; order: number }> = {
  initializing: { label: "Initializing...", order: 0 },
  starting_backend: { label: "Starting backend server...", order: 1 },
  waiting_health: { label: "Connecting to backend...", order: 2 },
  ready: { label: "Ready", order: 3 },
  error: { label: "Error", order: 99 },
};

const stageLabels: Record<string, string> = {
  initializing: "Starting Fixly...",
  starting_backend: "Starting backend server...",
  connecting_database: "Connecting to database...",
  checking_ollama: "Checking Ollama connection...",
  waiting_health: "Waiting for backend health check...",
  ready: "Ready!",
  error: "Startup failed",
};

function StageIndicator({ stage, currentStage }: { stage: string; currentStage: string }) {
  const stageInfo = STAGES[stage];
  const currentInfo = STAGES[currentStage];
  const isCompleted = currentInfo && stageInfo && currentInfo.order > stageInfo.order;
  const isActive = stage === currentStage;
  const isError = currentStage === "error";

  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-500 ${
          isCompleted
            ? "border-success bg-success/20 text-success"
            : isActive && !isError
              ? "border-primary bg-primary/20 text-primary"
              : isError && isActive
                ? "border-destructive bg-destructive/20 text-destructive"
                : "border-muted-foreground/30 text-muted-foreground/50"
        }`}
      >
        {isCompleted ? (
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : isActive && !isError ? (
          <div className="h-2 w-2 animate-pulse rounded-full bg-current" />
        ) : (
          <div className="h-2 w-2 rounded-full bg-current" />
        )}
      </div>
      <span
        className={`text-sm transition-colors duration-500 ${
          isCompleted
            ? "text-success"
            : isActive && !isError
              ? "text-foreground font-medium"
              : isError && isActive
                ? "text-destructive"
                : "text-muted-foreground/50"
        }`}
      >
        {stageLabels[stage] || stage}
      </span>
    </div>
  );
}

interface StartupScreenProps {
  status: StartupStatus | null;
  onRetry: () => void;
}

export function StartupScreen({ status, onRetry }: StartupScreenProps) {
  const currentStage = status?.stage || "initializing";
  const isError = currentStage === "error";
  const isReady = currentStage === "ready";

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background">
      <div className="mx-auto flex w-full max-w-sm flex-col items-center gap-8 px-6">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="flex flex-col items-center gap-4"
        >
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/20">
            <span className="text-4xl font-bold text-primary-foreground">F</span>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-foreground">Fixly</h1>
            <p className="text-sm text-muted-foreground">AI-powered academic operating system</p>
          </div>
        </motion.div>

        <div className="w-full space-y-4">
          {!isReady && (
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <motion.div
                className="h-full rounded-full bg-primary"
                initial={{ width: "0%" }}
                animate={
                  isError
                    ? { width: "100%", backgroundColor: "rgb(239, 68, 68)" }
                    : currentStage === "initializing"
                      ? { width: "10%" }
                      : currentStage === "starting_backend"
                        ? { width: "40%" }
                        : currentStage === "waiting_health"
                          ? { width: "70%" }
                          : { width: "90%" }
                }
                transition={{ duration: 0.8, ease: "easeInOut" }}
              />
            </div>
          )}

          <div className="space-y-3">
            {Object.keys(STAGES)
              .filter((s) => s !== "error")
              .map((stage) => (
                <StageIndicator key={stage} stage={stage} currentStage={currentStage} />
              ))}
            {isError && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 space-y-3"
              >
                <StageIndicator stage="error" currentStage={currentStage} />
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                  <p className="text-sm font-medium text-destructive">{status?.message}</p>
                  {status?.error && (
                    <p className="mt-1 text-xs text-muted-foreground">{status.error}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={onRetry}
                  className="inline-flex w-full items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                  Retry
                </button>
              </motion.div>
            )}
          </div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-xs text-muted-foreground/60"
        >
          v{typeof window !== "undefined" ? "1.0.0" : "1.0.0"}
        </motion.p>
      </div>
    </div>
  );
}

interface StartupGateProps {
  children: React.ReactNode;
}

export function StartupGate({ children }: StartupGateProps) {
  const [status, setStatus] = useState<StartupStatus | null>(null);
  const [ready, setReady] = useState(false);

  const checkStatus = useCallback(async () => {
    if (typeof window !== "undefined" && !(window as { __TAURI__?: unknown }).__TAURI__) {
      setReady(true);
      return;
    }

    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const result = await invoke<StartupStatus>("get_startup_status");
      setStatus(result);

      if (result.stage === "ready") {
        if (result.port) {
          const { setBackendPort } = await import("@/lib/api-client");
          setBackendPort(result.port);
        }
        setReady(true);
      }
    } catch {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 500);
    return () => clearInterval(interval);
  }, [checkStatus]);

  useEffect(() => {
    if (status?.stage === "error") {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [status, checkStatus]);

  if (ready) {
    return <>{children}</>;
  }

  return <StartupScreen status={status} onRetry={checkStatus} />;
}
