import apiClient from "@/lib/api-client";

export interface PlanResponse {
  plan_type: string;
  content: string;
  conversation_id: string;
  generated_at: string;
  context_summary?: Record<string, unknown>;
}

export interface BriefingFocusItem {
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  priority: "low" | "medium" | "high" | "urgent";
  type: string;
}

export interface DailyBriefing {
  date: string;
  greeting: string;
  summary: string;
  focus_items: BriefingFocusItem[];
  quote: { text: string; attribution: string };
  motivation: string;
  next_action: { label: string; target: string } | null;
  ai_available: boolean;
  generated_at: string;
  /** Local cache bookkeeping (never sent to the backend). */
  state_hash?: string;
}

export async function generateDailyPlan(): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/daily");
  return response.data;
}

export async function generateDailyBriefing(): Promise<DailyBriefing> {
  const response = await apiClient.post("/api/v1/ai/plan/daily/briefing");
  return response.data;
}

// ── Local briefing cache: one entry per user per date ──────────────

function cacheKey(userKey: string, date: string): string {
  return `fixly:briefing:${userKey}:${date}`;
}

function todayDate(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Fingerprint of the workspace state that matters for the briefing. */
export function briefingStateHash(input: {
  due_today?: number;
  pending?: number;
  overdue?: number;
  upcoming_count?: number;
}): string {
  return [
    input.due_today ?? 0,
    input.pending ?? 0,
    input.overdue ?? 0,
    input.upcoming_count ?? 0,
  ].join("|");
}

export function loadBriefingCache(userKey: string, stateHash: string): DailyBriefing | null {
  try {
    const raw = localStorage.getItem(cacheKey(userKey, todayDate()));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DailyBriefing;
    if (parsed.date !== todayDate()) return null;
    if (parsed.state_hash !== stateHash) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveBriefingCache(
  userKey: string,
  briefing: DailyBriefing,
  stateHash: string,
): void {
  try {
    localStorage.setItem(
      cacheKey(userKey, briefing.date),
      JSON.stringify({ ...briefing, state_hash: stateHash }),
    );
  } catch {
    // Storage full/blocked: briefing still works, just not cached.
  }
}

export function invalidateBriefingCache(userKey: string): void {
  try {
    localStorage.removeItem(cacheKey(userKey, todayDate()));
  } catch {
    // ignore
  }
}

export async function generateWeeklyPlan(): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/weekly");
  return response.data;
}

export async function generateRevisionPlan(subject_ids?: string[]): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/revision", { subject_ids });
  return response.data;
}

export async function listPlans(): Promise<PlanResponse[]> {
  const response = await apiClient.get("/api/v1/ai/plans");
  return response.data;
}
