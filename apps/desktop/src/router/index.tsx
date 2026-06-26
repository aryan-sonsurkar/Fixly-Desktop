import { createMemoryRouter, RouterProvider as ReactRouterProvider } from "react-router-dom";
import { PlaceholderRoute } from "@/components/placeholder-route";

const router = createMemoryRouter(
  [
    {
      path: "/",
      element: <PlaceholderRoute name="Dashboard" />,
    },
    {
      path: "/dashboard",
      element: <PlaceholderRoute name="Dashboard" />,
    },
    {
      path: "/assignments",
      element: <PlaceholderRoute name="Assignments" />,
    },
    {
      path: "/assignments/new",
      element: <PlaceholderRoute name="New Assignment" />,
    },
    {
      path: "/assignments/:id",
      element: <PlaceholderRoute name="Assignment Detail" />,
    },
    {
      path: "/ai",
      element: <PlaceholderRoute name="AI Assistant" />,
    },
    {
      path: "/pomodoro",
      element: <PlaceholderRoute name="Pomodoro" />,
    },
    {
      path: "/notifications",
      element: <PlaceholderRoute name="Notifications" />,
    },
    {
      path: "/analytics",
      element: <PlaceholderRoute name="Analytics" />,
    },
    {
      path: "/settings",
      element: <PlaceholderRoute name="Settings" />,
    },
    {
      path: "/login",
      element: <PlaceholderRoute name="Login" />,
    },
  ],
  {
    initialEntries: ["/dashboard"],
  },
);

export function RouterProvider() {
  return <ReactRouterProvider router={router} />;
}
