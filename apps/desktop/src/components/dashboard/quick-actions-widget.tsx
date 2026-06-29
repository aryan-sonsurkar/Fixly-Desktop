import { Link } from "react-router-dom";

interface QuickActionsWidgetProps {
  onOpenSearch: () => void;
}

export function QuickActionsWidget({ onOpenSearch }: QuickActionsWidgetProps) {
  const actions = [
    { label: "Start Pomodoro", to: "/pomodoro", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z", color: "text-red-500" },
    { label: "Study Diary", to: "/study", icon: "M13 10V3L4 14h7v7l9-11h-7z", color: "text-purple-500" },
    { label: "New Assignment", to: "/assignments", icon: "M12 4v16m8-8H4", color: "text-blue-500" },
    { label: "AI Study", to: "/ai", icon: "M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z", color: "text-green-500" },
  ];

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-2">
        {actions.map((a) => (
          <Link
            key={a.label}
            to={a.to}
            className="flex flex-col items-center gap-2 rounded-lg border bg-muted/30 p-3 text-sm transition-colors hover:bg-accent"
          >
            <svg className={`h-5 w-5 ${a.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d={a.icon} />
            </svg>
            <span className="text-xs">{a.label}</span>
          </Link>
        ))}
        <button
          type="button"
          onClick={onOpenSearch}
          className="col-span-2 flex items-center justify-center gap-2 rounded-lg border bg-muted/30 p-2 text-xs text-muted-foreground transition-colors hover:bg-accent"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          Search (Ctrl+K)
        </button>
      </div>
    </div>
  );
}
