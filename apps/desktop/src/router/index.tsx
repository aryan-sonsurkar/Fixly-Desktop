import { createMemoryRouter, RouterProvider as ReactRouterProvider } from "react-router-dom";
import { LoginPage } from "@/pages/login";
import { RegisterPage } from "@/pages/register";
import { ForgotPasswordPage } from "@/pages/forgot-password";
import { VerifyEmailPage } from "@/pages/verify-email";
import { OnboardingPage } from "@/pages/onboarding";
import { SettingsPage } from "@/pages/settings";
import { SubjectsPage } from "@/pages/subjects";
import { ProfilePage } from "@/pages/profile";
import { PlaceholderRoute } from "@/components/placeholder-route";
import { ProtectedRoute } from "@/components/protected-route";

function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <PlaceholderRoute name="App Layout" />
    </ProtectedRoute>
  );
}

const router = createMemoryRouter(
  [
    {
      path: "/login",
      element: <LoginPage />,
    },
    {
      path: "/register",
      element: <RegisterPage />,
    },
    {
      path: "/forgot-password",
      element: <ForgotPasswordPage />,
    },
    {
      path: "/verify-email",
      element: <VerifyEmailPage />,
    },
    {
      path: "/onboarding",
      element: <OnboardingPage />,
    },
    {
      path: "/",
      element: <ProtectedLayout />,
      children: [
        {
          index: true,
          element: <PlaceholderRoute name="Dashboard" />,
        },
        {
          path: "dashboard",
          element: <PlaceholderRoute name="Dashboard" />,
        },
        {
          path: "assignments",
          element: <PlaceholderRoute name="Assignments" />,
        },
        {
          path: "assignments/new",
          element: <PlaceholderRoute name="New Assignment" />,
        },
        {
          path: "assignments/:id",
          element: <PlaceholderRoute name="Assignment Detail" />,
        },
        {
          path: "ai",
          element: <PlaceholderRoute name="AI Assistant" />,
        },
        {
          path: "pomodoro",
          element: <PlaceholderRoute name="Pomodoro" />,
        },
        {
          path: "notifications",
          element: <PlaceholderRoute name="Notifications" />,
        },
        {
          path: "analytics",
          element: <PlaceholderRoute name="Analytics" />,
        },
        {
          path: "settings",
          element: <SettingsPage />,
        },
        {
          path: "subjects",
          element: <SubjectsPage />,
        },
        {
          path: "profile",
          element: <ProfilePage />,
        },
      ],
    },
  ],
  {
    initialEntries: ["/login"],
  },
);

export function RouterProvider() {
  return <ReactRouterProvider router={router} />;
}
