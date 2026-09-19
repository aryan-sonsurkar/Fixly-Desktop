import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BriefingWidget } from "@/components/dashboard/briefing-widget";
import type { DailyBriefing } from "@/lib/planner-service";

vi.mock("@fixly/ui", () => ({
  Button: ({ children, ...props }: { children: React.ReactNode }) => (
    <button {...props}>{children}</button>
  ),
  Skeleton: ({ className }: { className?: string }) => <div className={className} />,
}));

function briefing(): DailyBriefing {
  return {
    date: "2026-09-19",
    greeting: "Good morning, Aryan.",
    summary: "Focus on DBMS today.",
    focus_items: [
      { title: "DBMS Assignment", description: "", start_time: "17:00", end_time: "18:00", priority: "high", type: "assignment" },
      { title: "Revision", description: "", start_time: "19:00", end_time: "19:45", priority: "medium", type: "study" },
    ],
    quote: { text: "Keep going.", attribution: "Fixly AI" },
    motivation: "One focused session early helps.",
    next_action: { label: "Start Focus Session", target: "pomodoro" },
    ai_available: true,
    generated_at: "2026-09-19T00:00:00.000Z",
  };
}

describe("BriefingWidget", () => {
  it("renders structured briefing, never raw JSON", () => {
    const { container } = render(
      <BriefingWidget briefing={briefing()} loading={false} onGenerate={() => undefined} />,
    );
    expect(screen.getByText("AI Daily Briefing")).toBeTruthy();
    expect(screen.getByText("Good morning, Aryan.")).toBeTruthy();
    expect(screen.getByText("DBMS Assignment")).toBeTruthy();
    expect(screen.getByText(/Keep going/)).toBeTruthy();
    expect(screen.getByText("— Fixly AI")).toBeTruthy();
    expect(screen.getByText("Start Focus Session")).toBeTruthy();
    expect(container.textContent).not.toContain("schedule_items");
    expect(container.textContent).not.toContain('"priority"');
  });

  it("shows loading state", () => {
    render(<BriefingWidget briefing={null} loading onGenerate={() => undefined} />);
    expect(screen.getByText("Preparing your day...")).toBeTruthy();
  });

  it("shows empty state", () => {
    render(<BriefingWidget briefing={null} loading={false} onGenerate={() => undefined} />);
    expect(screen.getByText(/Generate your AI-powered daily briefing/)).toBeTruthy();
  });

  it("wires refresh and next-step actions", () => {
    const onGenerate = vi.fn();
    const onNextStep = vi.fn();
    render(
      <BriefingWidget briefing={briefing()} loading={false} onGenerate={onGenerate} onNextStep={onNextStep} />,
    );
    fireEvent.click(screen.getByText("Refresh"));
    fireEvent.click(screen.getByText("Start Focus Session"));
    expect(onGenerate).toHaveBeenCalledTimes(1);
    expect(onNextStep).toHaveBeenCalledTimes(1);
  });

  it("flags deterministic fallback when AI was unavailable", () => {
    render(
      <BriefingWidget briefing={{ ...briefing(), ai_available: false }} loading={false} onGenerate={() => undefined} />,
    );
    expect(screen.getByText(/AI was unavailable/)).toBeTruthy();
  });
});
