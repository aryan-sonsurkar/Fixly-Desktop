import { describe, expect, it } from "vitest";
import { focusReducer, initialFocusState, type FocusState } from "@/lib/focus-machine";
import type { CompanionAction } from "@/lib/companion-service";

const ACTION: CompanionAction = {
  kind: "assignment",
  key: "assignment:DBMS Revision:2026-10-03",
  title: "DBMS Revision",
  subject: "DBMS",
  due_date: "2026-10-03",
  overdue: false,
  priority: "high",
  suggested_minutes: 15,
  reason: "Due soonest.",
  document_id: null,
  document_name: null,
};

function suggested(base: Partial<FocusState> = {}): FocusState {
  return {
    ...initialFocusState,
    step: "suggested",
    action: ACTION,
    minutes: 10,
    ...base,
  };
}

describe("focus-machine micro-session", () => {
  it("starts idle with nothing selected", () => {
    expect(initialFocusState.step).toBe("idle");
    expect(initialFocusState.action).toBeNull();
  });

  it("suggest -> start -> practice -> check -> complete flows forward", () => {
    let s = focusReducer(initialFocusState, { type: "SUGGEST", action: ACTION, minutes: 10 });
    expect(s.step).toBe("suggested");
    s = focusReducer(s, { type: "START" });
    expect(s.step).toBe("active");
    s = focusReducer(s, { type: "PRACTICE" });
    expect(s.step).toBe("practice");
    s = focusReducer(s, { type: "CHECK" });
    expect(s.step).toBe("check");
    s = focusReducer(s, { type: "COMPLETE" });
    expect(s.step).toBe("done");
    expect(s.action).toBe(ACTION);
  });

  it("dismiss records the key so the next suggestion differs, then resets cleanly", () => {
    let s = suggested();
    s = focusReducer(s, { type: "DISMISS" });
    expect(s.step).toBe("idle");
    expect(s.action).toBeNull();
    expect(s.dismissedKeys).toEqual([ACTION.key]);
    s = focusReducer(s, { type: "RESET" });
    expect(s).toEqual({ ...initialFocusState, conversationId: null });
  });

  it("restore re-enters an interrupted session", () => {
    const s = focusReducer(initialFocusState, {
      type: "RESTORE",
      action: ACTION,
      conversationId: "conv-1",
    });
    expect(s.step).toBe("active");
    expect(s.action).toBe(ACTION);
    expect(s.conversationId).toBe("conv-1");
  });

  it("step events without an action are no-ops (exit is always safe)", () => {
    expect(focusReducer(initialFocusState, { type: "START" })).toBe(initialFocusState);
    expect(focusReducer(initialFocusState, { type: "COMPLETE" }).step).toBe("done");
  });
});
