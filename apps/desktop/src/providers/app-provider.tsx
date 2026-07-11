import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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

export function AppProvider() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <AnalyticsInit />
            <RouterProvider />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
