import { create } from "zustand";
import type { PomodoroSettingsData, PomodoroAnalyticsData } from "@/lib/pomodoro-service";

export type TimerPhase = "idle" | "focus" | "short_break" | "long_break";

export interface PomodoroState {
  phase: TimerPhase;
  timeRemaining: number;
  totalTime: number;
  cyclesCompleted: number;
  isRunning: boolean;
  settings: PomodoroSettingsData | null;
  analytics: PomodoroAnalyticsData | null;
  settingsOpen: boolean;
  analyticsOpen: boolean;
  sessionDialogOpen: boolean;

  setPhase: (phase: TimerPhase) => void;
  setTimeRemaining: (time: number) => void;
  setTotalTime: (time: number) => void;
  setCyclesCompleted: (cycles: number) => void;
  setIsRunning: (running: boolean) => void;
  setSettings: (settings: PomodoroSettingsData) => void;
  setAnalytics: (analytics: PomodoroAnalyticsData) => void;
  setSettingsOpen: (open: boolean) => void;
  setAnalyticsOpen: (open: boolean) => void;
  setSessionDialogOpen: (open: boolean) => void;
  reset: () => void;
}

const initialState = {
  phase: "idle" as TimerPhase,
  timeRemaining: 25 * 60,
  totalTime: 25 * 60,
  cyclesCompleted: 0,
  isRunning: false,
  settings: null,
  analytics: null,
  settingsOpen: false,
  analyticsOpen: false,
  sessionDialogOpen: false,
};

export const usePomodoroStore = create<PomodoroState>((set) => ({
  ...initialState,

  setPhase: (phase) => set({ phase }),
  setTimeRemaining: (time) => set({ timeRemaining: time }),
  setTotalTime: (time) => set({ totalTime: time }),
  setCyclesCompleted: (cycles) => set({ cyclesCompleted: cycles }),
  setIsRunning: (running) => set({ isRunning: running }),
  setSettings: (settings) => set({ settings }),
  setAnalytics: (analytics) => set({ analytics }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  setAnalyticsOpen: (open) => set({ analyticsOpen: open }),
  setSessionDialogOpen: (open) => set({ sessionDialogOpen: open }),
  reset: () => set(initialState),
}));
