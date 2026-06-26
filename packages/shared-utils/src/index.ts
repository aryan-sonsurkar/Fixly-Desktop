import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const APP_NAME = "Fixly";
export const API_VERSION = "v1";

export const STORAGE_KEYS = {
  THEME: "fixly-theme",
  AUTH_TOKEN: "fixly-auth-token",
  SIDEBAR_STATE: "fixly-sidebar-state",
} as const;

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...options,
  });
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

export function generateId(): string {
  return crypto.randomUUID();
}

export function isApiError(error: unknown): error is { response: { data: { error: string; code: string } } } {
  return (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof (error as Record<string, unknown>).response === "object"
  );
}
