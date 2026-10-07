import type { CompanionAction } from "@/lib/companion-service";

/** Micro-session steps. No timers, no schedules — the student can exit anywhere. */
export type FocusStep = "idle" | "suggested" | "active" | "practice" | "check" | "done";

export interface FocusState {
  step: FocusStep;
  action: CompanionAction | null;
  dismissedKeys: string[];
  minutes: number | null;
  conversationId: string | null;
}

export type FocusEvent =
  | { type: "SUGGEST"; action: CompanionAction; minutes: number | null; conversationId?: string | null }
  | { type: "START" }
  | { type: "PRACTICE" }
  | { type: "CHECK" }
  | { type: "COMPLETE" }
  | { type: "DISMISS" }
  | { type: "RESET" }
  | { type: "RESTORE"; action: CompanionAction; conversationId: string | null };

export const initialFocusState: FocusState = {
  step: "idle",
  action: null,
  dismissedKeys: [],
  minutes: null,
  conversationId: null,
};

export function focusReducer(state: FocusState, event: FocusEvent): FocusState {
  switch (event.type) {
    case "SUGGEST":
      return {
        ...state,
        step: "suggested",
        action: event.action,
        minutes: event.minutes,
        conversationId: event.conversationId ?? state.conversationId,
      };
    case "START":
      if (!state.action) return state;
      return { ...state, step: "active" };
    case "PRACTICE":
      if (!state.action) return state;
      return { ...state, step: "practice" };
    case "CHECK":
      if (!state.action) return state;
      return { ...state, step: "check" };
    case "COMPLETE":
      return { ...state, step: "done" };
    case "DISMISS":
      return {
        ...state,
        step: "idle",
        action: null,
        dismissedKeys: state.action ? [...state.dismissedKeys, state.action.key] : state.dismissedKeys,
      };
    case "RESET":
      return { ...initialFocusState, conversationId: state.conversationId };
    case "RESTORE":
      return {
        ...state,
        step: "active",
        action: event.action,
        conversationId: event.conversationId,
      };
    default:
      return state;
  }
}
