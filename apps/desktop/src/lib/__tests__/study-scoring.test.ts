import { describe, it, expect } from "vitest";
import {
  getPointsForActivity,
  calculateDailyGoalBonus,
  getHeatmapColor,
  calculateStreak,
  generateCalendar,
} from "@/lib/study-scoring";

describe("StudyScoring", () => {
  describe("getPointsForActivity", () => {
    it("returns 10 for pomodoro", () => {
      expect(getPointsForActivity("pomodoro")).toBe(10);
    });

    it("returns 25 for assignment", () => {
      expect(getPointsForActivity("assignment")).toBe(25);
    });

    it("returns 8 for ai_study", () => {
      expect(getPointsForActivity("ai_study")).toBe(8);
    });

    it("returns 0 for unknown activity", () => {
      expect(getPointsForActivity("unknown")).toBe(0);
    });

    it("has all required activities defined", () => {
      const required = ["pomodoro", "assignment", "ai_study", "reading", "manual"];
      for (const activity of required) {
        expect(getPointsForActivity(activity)).toBeGreaterThan(0);
      }
    });
  });

  describe("calculateDailyGoalBonus", () => {
    it("returns 15 when total points >= 50", () => {
      expect(calculateDailyGoalBonus(50)).toBe(15);
      expect(calculateDailyGoalBonus(100)).toBe(15);
    });

    it("returns 0 when total points < 50", () => {
      expect(calculateDailyGoalBonus(0)).toBe(0);
      expect(calculateDailyGoalBonus(49)).toBe(0);
    });
  });

  describe("getHeatmapColor", () => {
    it("returns muted bg for 0 points", () => {
      expect(getHeatmapColor(0)).toContain("muted");
    });

    it("returns light purple for 1-25 points", () => {
      expect(getHeatmapColor(1)).toContain("purple");
      expect(getHeatmapColor(25)).toContain("purple");
    });

    it("returns medium purple for 26-50 points", () => {
      expect(getHeatmapColor(26)).toContain("purple");
      expect(getHeatmapColor(50)).toContain("purple");
    });

    it("returns dark purple for 51-100 points", () => {
      expect(getHeatmapColor(51)).toContain("purple");
      expect(getHeatmapColor(100)).toContain("purple");
    });

    it("returns bright purple for 100+ points", () => {
      expect(getHeatmapColor(101)).toContain("purple");
      expect(getHeatmapColor(500)).toContain("purple");
    });
  });

  describe("calculateStreak", () => {
    it("returns 0 for empty dates", () => {
      expect(calculateStreak([])).toEqual({ current: 0, longest: 0 });
    });

    it("calculates current streak from today", () => {
      const today = new Date().toISOString().slice(0, 10);
      const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      expect(calculateStreak([today, yesterday]).current).toBeGreaterThanOrEqual(2);
    });

    it("calculates longest streak correctly", () => {
      const dates = [
        "2026-06-01", "2026-06-02", "2026-06-03",
        "2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08",
      ];
      const result = calculateStreak(dates);
      expect(result.longest).toBe(4);
    });

    it("returns current=0 when no active streak", () => {
      const dates = ["2026-06-01"];
      const result = calculateStreak(dates);
      const today = new Date().toISOString().slice(0, 10);
      if (today !== "2026-06-01") {
        expect(result.current).toBe(0);
      }
    });
  });

  describe("generateCalendar", () => {
    it("generates 365 or 366 days for a year", () => {
      const days = generateCalendar(2026);
      expect(days.length).toBeGreaterThanOrEqual(365);
      expect(days.length).toBeLessThanOrEqual(366);
    });

    it("all days have valid date strings", () => {
      const days = generateCalendar(2026);
      for (const d of days) {
        expect(d.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
        expect(d.dayOfWeek).toBeGreaterThanOrEqual(0);
        expect(d.dayOfWeek).toBeLessThanOrEqual(6);
      }
    });

    it("first day of the year is correct", () => {
      const days = generateCalendar(2026);
      expect(days[0].date).toBe("2026-01-01");
    });

    it("last day of the year is correct", () => {
      const days = generateCalendar(2026);
      const last = days[days.length - 1];
      expect(last.date).toBe("2026-12-31");
    });
  });
});
