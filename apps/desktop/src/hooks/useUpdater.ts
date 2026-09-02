import { useCallback, useEffect, useRef, useState } from "react";
import { createLogger } from "@/lib/logger";

const logger = createLogger("updater");

// Only run inside Tauri; no-op in browser/vite dev
function isTauri(): boolean {
  return typeof window !== "undefined" && (window as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ !== undefined;
}

export type UpdaterState =
  | { status: "idle" }
  | { status: "checking" }
  | { status: "available"; version: string; body?: string | null; date?: string | null }
  | { status: "downloading"; downloaded: number; total: number | null }
  | { status: "ready_to_restart"; version: string }
  | { status: "up_to_date" }
  | { status: "error"; message: string }
  | { status: "deferred"; version: string };

export function useUpdater() {
  const [state, setState] = useState<UpdaterState>({ status: "idle" });
  const dismissedRef = useRef<string | null>(null);

  const shouldDefer = useCallback((): boolean => {
    // Do not interrupt critical user flows
    try {
      const path = window.location.hash || window.location.pathname;
      // Pomodoro active, AI streaming, document upload — these are stored in zustand
      // For now, defer if the URL suggests an active flow where interruption is jarring
      if (path.includes("pomodoro")) {
        // Check if pomodoro is actually running via DOM or store
        const isRunning = document.querySelector("[data-pomodoro-running='true']");
        if (isRunning) return true;
      }
    } catch {
      // ignore
    }
    return false;
  }, []);

  const check = useCallback(async () => {
    if (!isTauri()) {
      logger.debug("Updater: not in Tauri, skipping check");
      return;
    }
    if (shouldDefer()) {
      logger.debug("Updater: deferring check — user in active flow");
      return;
    }
    setState({ status: "checking" });
    try {
      const { check } = await import("@tauri-apps/plugin-updater");
      const update = await check();
      if (!update) {
        setState({ status: "up_to_date" });
        logger.debug("Updater: up to date");
        return;
      }
      const version = (update as unknown as { version: string }).version ?? "unknown";
      const body = (update as unknown as { body?: string | null }).body ?? null;
      const date = (update as unknown as { date?: string | null }).date ?? null;

      if (dismissedRef.current === version) {
        setState({ status: "deferred", version });
        return;
      }
      logger.info("Updater: update available", { version });
      setState({ status: "available", version, body, date });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      // Network offline, malformed JSON, invalid signature — all handled as soft error, never crash
      if (message.includes("not found") || message.includes("404") || message.includes("Failed to fetch")) {
        logger.debug("Updater: no update or endpoint not yet published", { message });
        setState({ status: "up_to_date" });
        return;
      }
      logger.warn("Updater: check failed", { message });
      setState({ status: "error", message });
    }
  }, [shouldDefer]);

  const downloadAndInstall = useCallback(async () => {
    if (!isTauri()) return;
    const current = state;
    if (current.status !== "available") return;

    const version = current.version;
    setState({ status: "downloading", downloaded: 0, total: null });

    try {
      const { check } = await import("@tauri-apps/plugin-updater");
      const update = await check();
      if (!update) {
        setState({ status: "up_to_date" });
        return;
      }
      let downloaded = 0;
      let total: number | null = null;

      await (update as unknown as { downloadAndInstall: (cb?: (e: { event: string; data: { chunkLength: number } }) => void) => Promise<void> }).downloadAndInstall(
        (event) => {
          if (event.event === "Started") {
            total = (event.data as unknown as { contentLength?: number })?.contentLength ?? null;
          } else if (event.event === "Progress") {
            downloaded += (event.data as { chunkLength: number }).chunkLength;
            setState({ status: "downloading", downloaded, total });
          } else if (event.event === "Finished") {
            // no-op
          }
        },
      );
      setState({ status: "ready_to_restart", version });
      logger.info("Updater: downloaded, staged for next launch", { version });
      // Tauri updater stages the install; it applies on next launch.
      // We show "Restart to apply" instead of forcing relaunch to avoid interrupting active work.
      // The banner will handle the restart button via the updater's own relaunch if available,
      // otherwise the user restarts manually.
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      logger.error("Updater: download/install failed", { message });
      // Signature invalid, download interrupted, permissions — all are recoverable, do not corrupt install
      setState({ status: "error", message });
    }
  }, [state]);

  const dismiss = useCallback(() => {
    if (state.status === "available") {
      dismissedRef.current = state.version;
      setState({ status: "deferred", version: state.version });
    } else if (state.status === "error") {
      setState({ status: "idle" });
    }
  }, [state]);

  const retry = useCallback(() => {
    setState({ status: "idle" });
    void check();
  }, [check]);

  // Background check: after startup gate, wait 8s then check once
  useEffect(() => {
    if (!isTauri()) return;
    const t = setTimeout(() => void check(), 8000);
    return () => clearTimeout(t);
  }, [check]);

  return { state, check, downloadAndInstall, dismiss, retry, isTauri: isTauri() };
}
