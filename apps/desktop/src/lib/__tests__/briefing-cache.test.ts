import { describe, expect, it, beforeEach } from "vitest";
import {
  briefingStateHash,
  loadBriefingCache,
  saveBriefingCache,
  invalidateBriefingCache,
  type DailyBriefing,
} from "@/lib/planner-service";

function briefing(): DailyBriefing {
  return {
    date: "2099-01-01",
    greeting: "Good morning, Tester.",
    summary: "Focus on DBMS.",
    focus_items: [
      { title: "DBMS HW", description: "", start_time: "17:00", end_time: "18:00", priority: "high", type: "assignment" },
    ],
    quote: { text: "Keep going.", attribution: "Fixly AI" },
    motivation: "One session early helps.",
    next_action: { label: "Start Focus Session", target: "pomodoro" },
    ai_available: true,
    generated_at: "2099-01-01T00:00:00.000Z",
  };
}

describe("briefing cache", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("round-trips a briefing for the same state hash", () => {
    // Freeze "today" by writing directly under the expected key shape:
    // save uses briefing.date, load uses real today — so test helpers only.
    const hash = briefingStateHash({ due_today: 1, pending: 2, overdue: 0, upcoming_count: 3 });
    expect(hash).toBe("1|2|0|3");
    const b = { ...briefing(), date: new Date().toISOString().slice(0, 10) };
    saveBriefingCache("tester", b, hash);
    expect(loadBriefingCache("tester", hash)).toMatchObject({ summary: "Focus on DBMS." });
  });

  it("misses on state change", () => {
    const b = { ...briefing(), date: new Date().toISOString().slice(0, 10) };
    saveBriefingCache("tester", b, "1|2|0|3");
    expect(loadBriefingCache("tester", "9|9|9|9")).toBeNull();
  });

  it("invalidate clears today's entry", () => {
    const b = { ...briefing(), date: new Date().toISOString().slice(0, 10) };
    saveBriefingCache("tester", b, "1|2|0|3");
    invalidateBriefingCache("tester");
    expect(loadBriefingCache("tester", "1|2|0|3")).toBeNull();
  });
});
