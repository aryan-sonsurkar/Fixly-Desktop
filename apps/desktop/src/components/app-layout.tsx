import { Outlet, NavLink } from "react-router-dom";
import { useUIStore } from "@/stores/ui-store";
import { useAuthContext } from "@/contexts/auth-context";
import { Button } from "@fixly/ui";
import { cn } from "@fixly/shared-utils";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
  { to: "/assignments", label: "Assignments", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" },
  { to: "/subjects", label: "Subjects", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { to: "/pomodoro", label: "Pomodoro", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
  { to: "/analytics", label: "Analytics", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { to: "/settings", label: "Settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" },
];

const bottomNavItems = [
  { to: "/profile", label: "Profile", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
];

export function AppLayout() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user, signOut } = useAuthContext();

  return (
    <div className="flex h-screen bg-background">
      <aside
        className={cn(
          "flex flex-col border-r bg-card transition-all duration-300",
          sidebarOpen ? "w-56" : "w-16",
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b px-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            F
          </div>
          {sidebarOpen && <span className="text-sm font-semibold">Fixly</span>}
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="border-t p-2">
          {bottomNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}

          <button
            type="button"
            onClick={toggleSidebar}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <svg className={cn("h-5 w-5 shrink-0 transition-transform", sidebarOpen && "rotate-180")} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
            {sidebarOpen && <span className="truncate">Collapse</span>}
          </button>
        </div>
      </aside>

      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-end gap-3 border-b bg-card px-6">
          <div className="flex items-center gap-3">
            <NavLink
              to="/profile"
              className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                {(user?.profile?.full_name || user?.email || "U").charAt(0).toUpperCase()}
              </div>
              <span className="hidden md:inline truncate max-w-[120px]">
                {user?.profile?.full_name || user?.email}
              </span>
            </NavLink>
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
