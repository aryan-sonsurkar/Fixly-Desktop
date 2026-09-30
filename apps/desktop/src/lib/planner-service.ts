import apiClient from "@/lib/api-client";
import type {
  PlannerAction,
  PlannerActionType,
  PlanScheduleItem,
  Priority,
} from "@fixly/shared-types";

export type {
  PlannerAction,
  PlannerActionType,
  PlanScheduleItem,
};

export interface PlanResponse {
  plan_type: string;
  explanation?: string;
  actions?: PlannerAction[];
  schedule_items?: PlanScheduleItem[] | null;
  content: string;
  conversation_id: string;
  generated_at: string;
  context_summary?: Record<string, unknown>;
}

export interface ExecuteActionPayload {
  action_id: string;
  action: PlannerActionType;
  parameters: Record<string, unknown>;
  idempotency_key?: string;
}

export interface ExecuteActionResponse {
  success: boolean;
  action_id: string;
  action: string;
  message: string;
  result_data?: Record<string, unknown>;
}

const VALID_PRIORITIES = ["low", "medium", "high", "urgent"];
const VALID_TYPES = ["study", "break", "review", "assignment", "exam", "other"];

function extractJsonPayload(raw: string): string {
  let s = raw.trim();
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (fence) s = fence[1].trim();
  if (!s.startsWith("{") && !s.startsWith("[")) {
    const m = s.match(/(\{[\s\S]*\}|\[[\s\S]*\])/);
    if (m) s = m[1].trim();
  }
  return s;
}

function normalizePlanItem(item: unknown): PlanScheduleItem | null {
  if (!item || typeof item !== "object") return null;
  const o = item as Record<string, unknown>;
  const str = (v: unknown) => (typeof v === "string" ? v : "");
  const priority = str(o.priority).trim().toLowerCase();
  const type = str(o.type).trim().toLowerCase();
  if (!str(o.title) || !str(o.start_time) || !str(o.end_time)) return null;
  if (!VALID_PRIORITIES.includes(priority) || !VALID_TYPES.includes(type)) return null;
  return {
    title: str(o.title),
    description: str(o.description),
    start_time: str(o.start_time),
    end_time: str(o.end_time),
    priority: priority as Priority,
    type,
  };
}

/**
 * Display-layer recovery for plans reconstructed without `schedule_items`.
 * Drops unusable items. Returns [] when content is not a usable schedule.
 */
export function parseScheduleItems(content: string): PlanScheduleItem[] {
  let data: unknown;
  try {
    data = JSON.parse(extractJsonPayload(content));
  } catch {
    return [];
  }
  const rawItems = Array.isArray(data)
    ? data
    : data && typeof data === "object"
      ? (data as Record<string, unknown>).schedule_items
      : null;
  if (!Array.isArray(rawItems)) return [];
  const out: PlanScheduleItem[] = [];
  for (const raw of rawItems) {
    const item = normalizePlanItem(raw);
    if (item) out.push(item);
  }
  return out;
}

/**
 * Parses and validates structured actions from JSON content.
 */
export function parsePlannerActions(content: string): PlannerAction[] {
  let data: unknown;
  try {
    data = JSON.parse(extractJsonPayload(content));
  } catch {
    return [];
  }
  if (!data || typeof data !== "object") return [];
  const rawActions = Array.isArray(data)
    ? data
    : (data as Record<string, unknown>).actions;
  if (!Array.isArray(rawActions)) return [];
  const out: PlannerAction[] = [];
  for (const raw of rawActions) {
    if (!raw || typeof raw !== "object") continue;
    const a = raw as Record<string, unknown>;
    const actType = typeof a.action === "string" ? a.action.trim().toLowerCase() : "";
    const title = typeof a.title === "string" ? a.title.trim() : "";
    if (!title) continue;
    const action_id =
      typeof a.action_id === "string" && a.action_id
        ? a.action_id
        : `act_${Math.random().toString(36).slice(2, 9)}`;
    const priority = (
      typeof a.priority === "string" && VALID_PRIORITIES.includes(a.priority.trim().toLowerCase())
        ? a.priority.trim().toLowerCase()
        : "medium"
    ) as Priority;

    if (actType === "create_task") {
      out.push({
        action: "create_task",
        action_id,
        title,
        description: typeof a.description === "string" ? a.description : "",
        priority,
        due_date: typeof a.due_date === "string" ? a.due_date : null,
        estimated_minutes: typeof a.estimated_minutes === "number" ? a.estimated_minutes : null,
      });
    } else if (actType === "schedule_task") {
      if (typeof a.start_time !== "string" || typeof a.end_time !== "string") continue;
      out.push({
        action: "schedule_task",
        action_id,
        title,
        start_time: a.start_time,
        end_time: a.end_time,
        priority,
        type:
          typeof a.type === "string" && VALID_TYPES.includes(a.type.trim().toLowerCase())
            ? a.type.trim().toLowerCase()
            : "study",
        task_id: typeof a.task_id === "string" ? a.task_id : null,
      });
    } else if (actType === "create_study_session") {
      out.push({
        action: "create_study_session",
        action_id,
        title,
        duration_minutes: typeof a.duration_minutes === "number" ? a.duration_minutes : 25,
        scheduled_time: typeof a.scheduled_time === "string" ? a.scheduled_time : null,
        priority,
      });
    } else if (actType === "reschedule_task") {
      if (typeof a.new_start_time !== "string") continue;
      out.push({
        action: "reschedule_task",
        action_id,
        title,
        new_start_time: a.new_start_time,
        new_end_time: typeof a.new_end_time === "string" ? a.new_end_time : null,
        reason: typeof a.reason === "string" ? a.reason : "",
      });
    } else if (actType === "prioritize_task") {
      out.push({
        action: "prioritize_task",
        action_id,
        title,
        priority,
        reason: typeof a.reason === "string" ? a.reason : "",
      });
    }
  }
  return out;
}

/**
 * Synthesizes actionable structured cards from schedule items if actions were not provided.
 */
export function synthesizeActionsFromSchedule(items: PlanScheduleItem[]): PlannerAction[] {
  return items.map((item, idx) => {
    const aid = `act_synth_${idx}_${item.title.replace(/\s+/g, "_")}`;
    if (item.type === "study") {
      return {
        action: "create_study_session",
        action_id: aid,
        title: item.title,
        duration_minutes: 45,
        scheduled_time: item.start_time,
        priority: item.priority as Priority,
      };
    }
    if (item.type === "assignment") {
      return {
        action: "create_task",
        action_id: aid,
        title: item.title,
        description: item.description,
        priority: item.priority as Priority,
        due_date: item.end_time,
        estimated_minutes: 45,
      };
    }
    return {
      action: "schedule_task",
      action_id: aid,
      title: item.title,
      start_time: item.start_time,
      end_time: item.end_time,
      priority: item.priority as Priority,
      type: item.type,
    };
  });
}

/**
 * Extracts student-facing natural language explanation, stripping any raw JSON.
 */
export function extractExplanation(content: string): string {
  const s = content.trim();
  if (!s.startsWith("{") && !s.startsWith("[") && !s.startsWith("```")) {
    return s;
  }
  try {
    const parsed = JSON.parse(extractJsonPayload(content));
    if (
      parsed &&
      typeof parsed === "object" &&
      typeof parsed.explanation === "string" &&
      parsed.explanation.trim()
    ) {
      return parsed.explanation.trim();
    }
  } catch {
    // ignore
  }
  return "Here is your study plan with recommended actions based on your current workload.";
}

export async function executePlannerAction(
  action: PlannerAction,
  idempotencyKey?: string,
): Promise<ExecuteActionResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/execute-action", {
    action_id: action.action_id,
    action: action.action,
    parameters: action,
    idempotency_key: idempotencyKey || action.action_id,
  });
  return response.data;
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
  state_hash?: string;
}

export async function generateDailyPlan(): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/daily", undefined, { timeout: 300000 });
  return response.data;
}

export async function generateDailyBriefing(): Promise<DailyBriefing> {
  const response = await apiClient.post("/api/v1/ai/plan/daily/briefing", undefined, { timeout: 300000 });
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
    // Storage full/blocked
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
  const response = await apiClient.post("/api/v1/ai/plan/weekly", undefined, { timeout: 300000 });
  return response.data;
}

export async function generateRevisionPlan(subject_ids?: string[]): Promise<PlanResponse> {
  const response = await apiClient.post("/api/v1/ai/plan/revision", { subject_ids }, { timeout: 300000 });
  return response.data;
}

export async function listPlans(): Promise<PlanResponse[]> {
  const response = await apiClient.get("/api/v1/ai/plans");
  return response.data;
}

// ── Timeline display helpers ─────────────────────────────────

function parseDateTime(iso: string): Date | null {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

function startOfDay(d: Date): number {
  const c = new Date(d);
  c.setHours(0, 0, 0, 0);
  return c.getTime();
}

export function formatPlanTime(iso: string): string {
  const d = parseDateTime(iso);
  if (!d) return iso;
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function planDayLabel(iso: string): string {
  const d = parseDateTime(iso);
  if (!d) return "";
  const name = d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
  const diff = startOfDay(d) - startOfDay(new Date());
  if (diff === 0) return `Today · ${name}`;
  if (diff === 86400000) return `Tomorrow · ${name}`;
  if (diff < 0) return `${name} · past`;
  return name;
}

export function planDurationLabel(startIso: string, endIso: string): string | null {
  const s = parseDateTime(startIso);
  const e = parseDateTime(endIso);
  if (!s || !e) return null;
  const mins = Math.round((e.getTime() - s.getTime()) / 60000);
  if (mins <= 0) return null;
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

export function capitalizePlanWord(s: string): string {
  return s.length > 0 ? s[0].toUpperCase() + s.slice(1) : s;
}