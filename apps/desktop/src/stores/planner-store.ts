import { create } from "zustand";
import type { PlanResponse } from "@/lib/planner-service";

export interface PlannerState {
  dailyPlan: PlanResponse | null;
  weeklyPlan: PlanResponse | null;
  revisionPlan: PlanResponse | null;
  loadingDaily: boolean;
  loadingWeekly: boolean;
  loadingRevision: boolean;
  activeView: "daily" | "weekly" | "revision";
  setDailyPlan: (plan: PlanResponse | null) => void;
  setWeeklyPlan: (plan: PlanResponse | null) => void;
  setRevisionPlan: (plan: PlanResponse | null) => void;
  setLoadingDaily: (loading: boolean) => void;
  setLoadingWeekly: (loading: boolean) => void;
  setLoadingRevision: (loading: boolean) => void;
  setActiveView: (view: "daily" | "weekly" | "revision") => void;
  reset: () => void;
}

export const usePlannerStore = create<PlannerState>((set) => ({
  dailyPlan: null,
  weeklyPlan: null,
  revisionPlan: null,
  loadingDaily: false,
  loadingWeekly: false,
  loadingRevision: false,
  activeView: "daily",

  setDailyPlan: (plan) => set({ dailyPlan: plan }),
  setWeeklyPlan: (plan) => set({ weeklyPlan: plan }),
  setRevisionPlan: (plan) => set({ revisionPlan: plan }),
  setLoadingDaily: (loading) => set({ loadingDaily: loading }),
  setLoadingWeekly: (loading) => set({ loadingWeekly: loading }),
  setLoadingRevision: (loading) => set({ loadingRevision: loading }),
  setActiveView: (view) => set({ activeView: view }),
  reset: () =>
    set({
      dailyPlan: null,
      weeklyPlan: null,
      revisionPlan: null,
      loadingDaily: false,
      loadingWeekly: false,
      loadingRevision: false,
      activeView: "daily",
    }),
}));
