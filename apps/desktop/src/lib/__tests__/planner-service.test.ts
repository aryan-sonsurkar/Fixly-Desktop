import { describe, expect, it } from "vitest";

import {
  capitalizePlanWord,
  extractExplanation,
  formatPlanTime,
  parsePlannerActions,
  parseScheduleItems,
  planDayLabel,
  planDurationLabel,
  synthesizeActionsFromSchedule,
} from "@/lib/planner-service";

const VALID = JSON.stringify({
  schedule_items: [
    {
      title: "DBMS Normalization",
      description: "Read chapter 3",
      start_time: "2026-09-28T21:00:00Z",
      end_time: "2026-09-28T22:00:00Z",
      priority: "high",
      type: "study",
    },
    {
      title: "Break",
      description: "",
      start_time: "2026-09-28T22:00:00Z",
      end_time: "2026-09-28T22:15:00Z",
      priority: "low",
      type: "break",
    },
  ],
});

const VALID_ACTIONS_JSON = JSON.stringify({
  explanation: "Focus on Normalization for tonight's exam preparation.",
  actions: [
    {
      action: "create_study_session",
      action_id: "act_1",
      title: "DBMS Normalization",
      duration_minutes: 45,
      priority: "high",
    },
    {
      action: "create_task",
      action_id: "act_2",
      title: "Revise SQL joins",
      priority: "medium",
      estimated_minutes: 30,
    },
    {
      action: "schedule_task",
      action_id: "act_3",
      title: "Practice questions",
      start_time: "2026-09-28T22:00:00Z",
      end_time: "2026-09-28T22:30:00Z",
      priority: "high",
      type: "study",
    },
  ],
});

describe("parseScheduleItems (display-layer schedule recovery)", () => {
  it("parses our own valid schedule JSON", () => {
    const items = parseScheduleItems(VALID);
    expect(items).toHaveLength(2);
    expect(items[0].title).toBe("DBMS Normalization");
    expect(items[1].priority).toBe("low");
  });

  it("parses fenced payloads", () => {
    expect(parseScheduleItems("```json\n" + VALID + "\n```")).toHaveLength(2);
  });

  it("drops echoed option lists and keeps valid siblings", () => {
    const mixed = JSON.stringify({
      schedule_items: [
        {
          title: "Good",
          description: "",
          start_time: "2026-09-28T21:00:00Z",
          end_time: "2026-09-28T22:00:00Z",
          priority: "high",
          type: "study",
        },
        {
          title: "Bad",
          description: "",
          start_time: "2026-09-28T21:00:00Z",
          end_time: "2026-09-28T22:00:00Z",
          priority: "low|medium|high|urgent",
          type: "study|break|review",
        },
      ],
    });
    const items = parseScheduleItems(mixed);
    expect(items.map((i) => i.title)).toEqual(["Good"]);
  });

  it("normalizes case/whitespace near-misses", () => {
    const near = JSON.stringify({
      schedule_items: [
        {
          title: "T",
          description: "",
          start_time: "2026-09-28T21:00:00Z",
          end_time: "2026-09-28T22:00:00Z",
          priority: " High ",
          type: "STUDY",
        },
      ],
    });
    const items = parseScheduleItems(near);
    expect(items).toHaveLength(1);
    expect(items[0].priority).toBe("high");
    expect(items[0].type).toBe("study");
  });

  it("returns [] for prose and garbage (callers show text or error)", () => {
    expect(parseScheduleItems("Study DBMS tonight, then rest.")).toEqual([]);
    expect(parseScheduleItems("not json at all {{{")).toEqual([]);
    expect(parseScheduleItems('{"schedule_items": []}')).toEqual([]);
  });
});

describe("parsePlannerActions (structured action parsing)", () => {
  it("parses valid actions from canonical JSON", () => {
    const actions = parsePlannerActions(VALID_ACTIONS_JSON);
    expect(actions).toHaveLength(3);
    expect(actions[0].action).toBe("create_study_session");
    expect(actions[0].title).toBe("DBMS Normalization");
    expect(actions[1].action).toBe("create_task");
    expect(actions[1].title).toBe("Revise SQL joins");
    expect(actions[2].action).toBe("schedule_task");
  });

  it("drops unknown actions while preserving valid ones", () => {
    const mixed = JSON.stringify({
      actions: [
        { action: "unknown_hack", title: "Should be dropped" },
        { action: "create_task", title: "Valid Task", priority: "medium" },
      ],
    });
    const actions = parsePlannerActions(mixed);
    expect(actions).toHaveLength(1);
    expect(actions[0].title).toBe("Valid Task");
  });

  it("assigns action_id if omitted in model output", () => {
    const payload = JSON.stringify({
      actions: [{ action: "create_task", title: "No Action ID", priority: "high" }],
    });
    const actions = parsePlannerActions(payload);
    expect(actions).toHaveLength(1);
    expect(actions[0].action_id).toBeDefined();
    expect(actions[0].action_id.startsWith("act_")).toBe(true);
  });
});

describe("synthesizeActionsFromSchedule", () => {
  it("synthesizes study session actions and schedule actions from timeline items", () => {
    const items = parseScheduleItems(VALID);
    const actions = synthesizeActionsFromSchedule(items);
    expect(actions).toHaveLength(2);
    expect(actions[0].action).toBe("create_study_session");
    expect(actions[0].title).toBe("DBMS Normalization");
    expect(actions[1].action).toBe("schedule_task");
    expect(actions[1].title).toBe("Break");
  });
});

describe("extractExplanation", () => {
  it("extracts explanation field from JSON payload", () => {
    const exp = extractExplanation(VALID_ACTIONS_JSON);
    expect(exp).toBe("Focus on Normalization for tonight's exam preparation.");
  });

  it("never returns raw JSON braces for JSON payloads lacking explanation", () => {
    const exp = extractExplanation(VALID);
    expect(exp.startsWith("{")).toBe(false);
    expect(exp).toContain("study plan");
  });

  it("passes pure prose through cleanly", () => {
    const prose = "I recommend you spend 45 minutes on normalization tonight.";
    expect(extractExplanation(prose)).toBe(prose);
  });
});

describe("timeline display helpers", () => {
  it("formats times and passes through garbage", () => {
    expect(formatPlanTime("2026-09-28T21:30:00Z")).toMatch(/\d{1,2}:\d{2}/);
    expect(formatPlanTime("not-a-date")).toBe("not-a-date");
  });

  it("labels today/tomorrow/past days", () => {
    const now = new Date();
    const iso = (d: Date) => d.toISOString();
    const today = planDayLabel(iso(now));
    expect(today.startsWith("Today · ")).toBe(true);
    const tomorrow = new Date(now.getTime() + 86400000);
    expect(planDayLabel(iso(tomorrow)).startsWith("Tomorrow · ")).toBe(true);
    const past = new Date(now.getTime() - 30 * 86400000);
    expect(planDayLabel(iso(past))).toContain("past");
    expect(planDayLabel("garbage")).toBe("");
  });

  it("computes durations and rejects inverted ranges", () => {
    expect(planDurationLabel("2026-09-28T21:00:00Z", "2026-09-28T21:45:00Z")).toBe("45m");
    expect(planDurationLabel("2026-09-28T21:00:00Z", "2026-09-28T22:30:00Z")).toBe("1h 30m");
    expect(planDurationLabel("2026-09-28T21:30:00Z", "2026-09-28T20:30:00Z")).toBeNull();
    expect(planDurationLabel("bad", "2026-09-28T20:30:00Z")).toBeNull();
  });

  it("capitalizes labels", () => {
    expect(capitalizePlanWord("high")).toBe("High");
    expect(capitalizePlanWord("")).toBe("");
  });
});
