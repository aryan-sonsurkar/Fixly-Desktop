import { useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthContext } from "@/contexts/auth-context";
import { checkOnboardingStatus } from "@/lib/profile-service";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthContext();
  const location = useLocation();
  const [onboardingStatus, setOnboardingStatus] = useState<"loading" | "done" | "pending">("loading");

  useEffect(() => {
    if (!isAuthenticated || isLoading) return;
    async function check() {
      try {
        const status = await checkOnboardingStatus();
        setOnboardingStatus(status.onboarding_completed ? "done" : "pending");
      } catch {
        setOnboardingStatus("done");
      }
    }
    check();
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (onboardingStatus === "loading") {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (onboardingStatus === "pending" && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}
