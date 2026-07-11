type LogLevel = "debug" | "info" | "warn" | "error";

declare const __TAURI__: unknown;

class Logger {
  private context: string;

  constructor(context: string) {
    this.context = context;
  }

  private format(level: LogLevel, message: string, ...args: unknown[]) {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}] [${this.context}]`;
    const method = level === "error" ? "error" : level === "warn" ? "warn" : "log";
    console[method](prefix, message, ...args);

    if (level === "error" && typeof __TAURI__ === "undefined") {
      try {
        import("@/stores/analytics-store").then(({ useAnalyticsStore }) => {
          useAnalyticsStore.getState().trackEvent("error", {
            context: this.context,
            message,
            args: args.length > 0 ? JSON.stringify(args).substring(0, 200) : undefined,
          });
        });
      } catch { /* analytics unavailable */ }
    }
  }

  debug(message: string, ...args: unknown[]) {
    this.format("debug", message, ...args);
  }

  info(message: string, ...args: unknown[]) {
    this.format("info", message, ...args);
  }

  warn(message: string, ...args: unknown[]) {
    this.format("warn", message, ...args);
  }

  error(message: string, ...args: unknown[]) {
    this.format("error", message, ...args);
  }
}

const loggers = new Map<string, Logger>();

export function createLogger(context: string): Logger {
  if (!loggers.has(context)) {
    loggers.set(context, new Logger(context));
  }
  return loggers.get(context)!;
}
