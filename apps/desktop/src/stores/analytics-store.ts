import { create } from "zustand";

export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, unknown>;
  timestamp: string;
}

interface AnalyticsState {
  events: AnalyticsEvent[];
  sessionStart: string | null;
  appLaunches: number;
  sessionCount: number;
  trackEvent: (name: string, properties?: Record<string, unknown>) => void;
  startSession: () => void;
  endSession: () => void;
  incrementLaunches: () => void;
  flush: () => AnalyticsEvent[];
}

function loadPersisted(): { appLaunches: number; events: AnalyticsEvent[] } {
  try {
    const raw = localStorage.getItem("fixly_analytics");
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        appLaunches: parsed.appLaunches || 0,
        events: parsed.events?.slice(-200) || [],
      };
    }
  } catch { /* ignore */ }
  return { appLaunches: 0, events: [] };
}

function persist(state: Pick<AnalyticsState, "appLaunches" | "events">) {
  try {
    localStorage.setItem(
      "fixly_analytics",
      JSON.stringify({ appLaunches: state.appLaunches, events: state.events.slice(-200) }),
    );
  } catch { /* ignore */ }
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => {
  const persisted = loadPersisted();
  return {
    events: persisted.events,
    sessionStart: null,
    appLaunches: persisted.appLaunches,
    sessionCount: 0,

    trackEvent: (name, properties) => {
      const event: AnalyticsEvent = { name, properties, timestamp: new Date().toISOString() };
      set((s) => {
        const events = [...s.events, event].slice(-500);
        persist({ appLaunches: s.appLaunches, events });
        return { events };
      });
    },

    startSession: () => {
      set((s) => ({ sessionStart: new Date().toISOString(), sessionCount: s.sessionCount + 1 }));
    },

    endSession: () => {
      const { sessionStart } = get();
      if (sessionStart) {
        const duration = Date.now() - new Date(sessionStart).getTime();
        get().trackEvent("session_end", { duration_ms: duration });
        set({ sessionStart: null });
      }
    },

    incrementLaunches: () => {
      set((s) => {
        const appLaunches = s.appLaunches + 1;
        persist({ appLaunches, events: s.events });
        return { appLaunches };
      });
    },

    flush: () => get().events,
  };
});
