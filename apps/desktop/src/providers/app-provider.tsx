import { useEffect } from "react";
import { QueryClient, QueryClientProvider, dehydrate, hydrate } from "@tanstack/react-query";
import { ThemeProvider } from "@/providers/theme-provider";
import { ErrorBoundary } from "@/components/error-boundary";
import { AuthProvider } from "@/contexts/auth-context";
import { RouterProvider } from "@/router";
import { useAnalyticsStore } from "@/stores/analytics-store";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
      gcTime: 10 * 60 * 1000,
    },
  },
});

function AnalyticsInit() {
  const incrementLaunches = useAnalyticsStore((s) => s.incrementLaunches);
  const startSession = useAnalyticsStore((s) => s.startSession);
  const endSession = useAnalyticsStore((s) => s.endSession);
  const trackEvent = useAnalyticsStore((s) => s.trackEvent);

  useEffect(() => {
    incrementLaunches();
    startSession();
    trackEvent("app_launch", { timestamp: new Date().toISOString() });

    return () => {
      endSession();
    };
  }, [incrementLaunches, startSession, endSession, trackEvent]);

  return null;
}

const QUERY_CACHE_KEY = "fixly:query-cache-v2";
function InstantPrefetch() {
  useEffect(() => {
    // restore cache -> cold restart still instant (persist)
    try {
      const raw = localStorage.getItem(QUERY_CACHE_KEY);
      if (raw) hydrate(queryClient, JSON.parse(raw));
    } catch (_e) { /* ignore corrupt cache */ }
    // persist on every success
    const unsub = queryClient.getQueryCache().subscribe(() => {
      try {
        const data = dehydrate(queryClient, { shouldDehydrateQuery: (q) => q.state.status === "success" });
        // cap to 1MB to avoid quota
        const json = JSON.stringify(data);
        if (json.length < 900_000) localStorage.setItem(QUERY_CACHE_KEY, json);
      } catch (_e) { /* ignore quota */ }
    });
    // prefetch after idle so every page feels instant on first click — no skeleton
    const t = setTimeout(() => {
      import("@/lib/profile-service").then(({ getSubjects, getMySettings, getMyProfile }) => {
        void queryClient.prefetchQuery({ queryKey: ["subjects"], queryFn: getSubjects, staleTime: 60 * 1000 });
        void queryClient.prefetchQuery({ queryKey: ["settings"], queryFn: getMySettings, staleTime: 60 * 1000 });
        void queryClient.prefetchQuery({ queryKey: ["profile"], queryFn: getMyProfile, staleTime: 60 * 1000 });
      });
      import("@/lib/document-service").then(({ listDocuments }) => {
        void queryClient.prefetchQuery({ queryKey: ["documents", "", null], queryFn: () => listDocuments({ page_size: 50 }), staleTime: 30 * 1000 });
      });
      import("@/lib/pomodoro-service").then(({ getPomodoroSettings, getPomodoroAnalytics }) => {
        void queryClient.prefetchQuery({ queryKey: ["pomodoro-settings"], queryFn: getPomodoroSettings, staleTime: 60 * 1000 });
        void queryClient.prefetchQuery({ queryKey: ["pomodoro-analytics"], queryFn: getPomodoroAnalytics, staleTime: 30 * 1000 });
      });
      import("@/lib/study-service").then(({ getCalendar, getStudyStatistics }) => {
        void queryClient.prefetchQuery({ queryKey: ["study-calendar", new Date().getFullYear()], queryFn: () => getCalendar(new Date().getFullYear()), staleTime: 60 * 1000 });
        void queryClient.prefetchQuery({ queryKey: ["study-statistics"], queryFn: getStudyStatistics, staleTime: 60 * 1000 });
      });
      import("@/lib/email-service").then(({ getEmailAccounts, getEmailMessages }) => {
        void queryClient.prefetchQuery({ queryKey: ["email-accounts"], queryFn: getEmailAccounts, staleTime: 60 * 1000 });
        void queryClient.prefetchQuery({ queryKey: ["email-messages", ""], queryFn: () => getEmailMessages({ page_size: 50 }), staleTime: 30 * 1000 });
      });
      import("@/lib/diagnostics-service").then(({ getDiagnostics }) => {
        void queryClient.prefetchQuery({ queryKey: ["diagnostics"], queryFn: getDiagnostics, staleTime: 30 * 1000 });
      });
    }, 900);
    return () => { clearTimeout(t); unsub(); };
  }, []);
  return null;
}

export function AppProvider() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <AnalyticsInit />
            <InstantPrefetch />
            <RouterProvider />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
