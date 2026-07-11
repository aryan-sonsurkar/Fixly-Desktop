import { lazy, Suspense } from "react";
import { createMemoryRouter, RouterProvider as ReactRouterProvider } from "react-router-dom";
import { Skeleton } from "@fixly/ui";
import { ProtectedRoute } from "@/components/protected-route";
import { AppLayout } from "@/components/app-layout";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";

const LoginPage = lazy(() => import("@/pages/login").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/register").then((m) => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import("@/pages/forgot-password").then((m) => ({ default: m.ForgotPasswordPage })));
const VerifyEmailPage = lazy(() => import("@/pages/verify-email").then((m) => ({ default: m.VerifyEmailPage })));
const OnboardingPage = lazy(() => import("@/pages/onboarding").then((m) => ({ default: m.OnboardingPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard").then((m) => ({ default: m.DashboardPage })));
const AssignmentsPage = lazy(() => import("@/pages/assignments").then((m) => ({ default: m.AssignmentsPage })));
const AIPage = lazy(() => import("@/pages/ai"));
const StudyPage = lazy(() => import("@/pages/study").then((m) => ({ default: m.StudyPage })));
const EmailPage = lazy(() => import("@/pages/email").then((m) => ({ default: m.EmailPage })));
const PomodoroPage = lazy(() => import("@/pages/pomodoro").then((m) => ({ default: m.PomodoroPage })));
const DocumentsPage = lazy(() => import("@/pages/documents").then((m) => ({ default: m.DocumentsPage })));
const SettingsPage = lazy(() => import("@/pages/settings").then((m) => ({ default: m.SettingsPage })));
const SubjectsPage = lazy(() => import("@/pages/subjects").then((m) => ({ default: m.SubjectsPage })));
const ProfilePage = lazy(() => import("@/pages/profile").then((m) => ({ default: m.ProfilePage })));
const NotificationPage = lazy(() => import("@/pages/notifications").then((m) => ({ default: m.NotificationPage })));
const PlannerPage = lazy(() => import("@/pages/planner").then((m) => ({ default: m.PlannerPage })));
const DiagnosticsPage = lazy(() => import("@/pages/diagnostics").then((m) => ({ default: m.DiagnosticsPage })));

function NotFoundPage() {
  return (
    <div className="flex h-screen items-center justify-center bg-background p-6">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
        <p className="mt-2 text-lg text-muted-foreground">Page not found</p>
        <a
          href="/dashboard"
          className="mt-4 inline-flex items-center gap-2 text-sm text-primary hover:underline"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to dashboard
        </a>
      </div>
    </div>
  );
}

function LazyLoad({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="p-6 space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-64" /><div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div></div>}>
      {children}
    </Suspense>
  );
}

function ProtectedLayout() {
  useKeyboardShortcuts();
  return (
    <ProtectedRoute>
      <AppLayout />
    </ProtectedRoute>
  );
}

const router = createMemoryRouter(
  [
    { path: "/login", element: <LazyLoad><LoginPage /></LazyLoad> },
    { path: "/register", element: <LazyLoad><RegisterPage /></LazyLoad> },
    { path: "/forgot-password", element: <LazyLoad><ForgotPasswordPage /></LazyLoad> },
    { path: "/verify-email", element: <LazyLoad><VerifyEmailPage /></LazyLoad> },
    { path: "/onboarding", element: <LazyLoad><OnboardingPage /></LazyLoad> },
    {
      path: "/",
      element: <ProtectedLayout />,
      children: [
        { index: true, element: <LazyLoad><DashboardPage /></LazyLoad> },
        { path: "dashboard", element: <LazyLoad><DashboardPage /></LazyLoad> },
        { path: "assignments", element: <LazyLoad><AssignmentsPage /></LazyLoad> },
        { path: "ai", element: <LazyLoad><AIPage /></LazyLoad> },
        { path: "pomodoro", element: <LazyLoad><PomodoroPage /></LazyLoad> },
        { path: "documents", element: <LazyLoad><DocumentsPage /></LazyLoad> },
        { path: "notifications", element: <LazyLoad><NotificationPage /></LazyLoad> },
        { path: "email", element: <LazyLoad><EmailPage /></LazyLoad> },
        { path: "planner", element: <LazyLoad><PlannerPage /></LazyLoad> },
        { path: "study", element: <LazyLoad><StudyPage /></LazyLoad> },
        { path: "settings", element: <LazyLoad><SettingsPage /></LazyLoad> },
        { path: "subjects", element: <LazyLoad><SubjectsPage /></LazyLoad> },
        { path: "profile", element: <LazyLoad><ProfilePage /></LazyLoad> },
        { path: "diagnostics", element: <LazyLoad><DiagnosticsPage /></LazyLoad> },
      ],
    },
    { path: "*", element: <NotFoundPage /> },
  ],
  { initialEntries: ["/login"] },
);

export function RouterProvider() {
  return <ReactRouterProvider router={router} />;
}
