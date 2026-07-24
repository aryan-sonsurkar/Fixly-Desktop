import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@fixly/ui";

const shortcutGroups = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: "g + d", label: "Dashboard" },
      { keys: "g + a", label: "Assignments" },
      { keys: "g + i", label: "AI Workspace" },
      { keys: "g + s", label: "Subjects" },
      { keys: "g + p", label: "Pomodoro" },
      { keys: "g + o", label: "Documents" },
      { keys: "g + e", label: "Email" },
      { keys: "g + l", label: "Planner" },
      { keys: "g + y", label: "Study" },
      { keys: "g + n", label: "Notifications" },
      { keys: "g + r", label: "Profile" },
    ],
  },
  {
    title: "General",
    shortcuts: [
      { keys: "Ctrl+K", label: "Command palette / Search" },
      { keys: "Escape", label: "Close dialogs" },
      { keys: "?", label: "Show this help" },
    ],
  },
];

export function KeyboardShortcutsDialog() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "?" && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const target = e.target as HTMLElement;
        const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT" || target.isContentEditable;
        if (!isInput) {
          e.preventDefault();
          setOpen(true);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="space-y-6">
          {shortcutGroups.map((group) => (
            <div key={group.title}>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {group.title}
              </h4>
              <div className="space-y-1.5">
                {group.shortcuts.map((item) => (
                  <div
                    key={item.keys}
                    className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm"
                  >
                    <span className="text-muted-foreground">{item.label}</span>
                    <kbd className="rounded border bg-muted px-2 py-0.5 font-mono text-xs">
                      {item.keys}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
