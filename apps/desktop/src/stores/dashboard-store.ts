import { create } from "zustand";
import type { DashboardData } from "@/lib/dashboard-service";
import type { PlanResponse } from "@/lib/planner-service";

export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  visible: boolean;
  order: number;
  size: "small" | "medium" | "large" | "full";
}

export interface DashboardState {
  data: DashboardData | null;
  briefing: PlanResponse | null;
  loading: boolean;
  briefingLoading: boolean;
  widgets: DashboardWidget[];
  setData: (data: DashboardData | null) => void;
  setBriefing: (briefing: PlanResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setBriefingLoading: (loading: boolean) => void;
  setWidgets: (widgets: DashboardWidget[]) => void;
  updateWidget: (id: string, updates: Partial<DashboardWidget>) => void;
  reorderWidgets: (widgets: DashboardWidget[]) => void;
  toggleWidgetVisibility: (id: string) => void;
}

const DEFAULT_WIDGETS: DashboardWidget[] = [
  { id: "briefing", type: "briefing", title: "AI Daily Briefing", visible: true, order: 0, size: "full" },
  { id: "focus", type: "focus", title: "Today's Focus", visible: true, order: 1, size: "small" },
  { id: "tasks", type: "tasks", title: "AI Recommended Tasks", visible: true, order: 2, size: "small" },
  { id: "assignments", type: "assignments", title: "Upcoming Assignments", visible: true, order: 3, size: "medium" },
  { id: "exams", type: "exams", title: "Upcoming Exams", visible: true, order: 4, size: "small" },
  { id: "documents", type: "documents", title: "Recent Documents", visible: true, order: 5, size: "small" },
  { id: "emails", type: "emails", title: "Recent Emails", visible: true, order: 6, size: "small" },
  { id: "pomodoro", type: "pomodoro", title: "Current Pomodoro", visible: true, order: 7, size: "small" },
  { id: "heatmap", type: "heatmap", title: "Study Heatmap", visible: true, order: 8, size: "medium" },
  { id: "progress", type: "progress", title: "Weekly Progress", visible: true, order: 9, size: "medium" },
  { id: "xp", type: "xp", title: "XP & Streak", visible: true, order: 10, size: "small" },
  { id: "score", type: "score", title: "Productivity Score", visible: true, order: 11, size: "small" },
  { id: "actions", type: "actions", title: "Quick Actions", visible: true, order: 12, size: "medium" },
];

export const useDashboardStore = create<DashboardState>((set) => ({
  data: null,
  briefing: null,
  loading: true,
  briefingLoading: false,
  widgets: DEFAULT_WIDGETS,

  setData: (data) => set({ data }),
  setBriefing: (briefing) => set({ briefing }),
  setLoading: (loading) => set({ loading }),
  setBriefingLoading: (loading) => set({ briefingLoading: loading }),
  setWidgets: (widgets) => set({ widgets }),
  updateWidget: (id, updates) =>
    set((state) => ({
      widgets: state.widgets.map((w) => (w.id === id ? { ...w, ...updates } : w)),
    })),
  reorderWidgets: (widgets) => set({ widgets }),
  toggleWidgetVisibility: (id) =>
    set((state) => ({
      widgets: state.widgets.map((w) =>
        w.id === id ? { ...w, visible: !w.visible } : w,
      ),
    })),
}));
