import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSearchStore } from "@/stores/search-store";
import { useNotificationStore } from "@/stores/notification-store";
import { getUnreadCount } from "@/lib/notification-service";

const NAV_SHORTCUTS: Record<string, string> = {
  "gd": "/dashboard",
  "ga": "/assignments",
  "gi": "/ai",
  "gs": "/subjects",
  "gp": "/pomodoro",
  "go": "/documents",
  "ge": "/email",
  "gl": "/planner",
  "gy": "/study",
  "gn": "/notifications",
  "gr": "/profile",
};

export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { setOpen: setSearchOpen } = useSearchStore();
  const { setUnreadCount } = useNotificationStore();

  useEffect(() => {
    let keyBuffer = "";
    let bufferTimeout: ReturnType<typeof setTimeout> | null = null;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT" || target.isContentEditable;

      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
        return;
      }

      if (e.key === "Escape") {
        const modal = document.querySelector('[role="dialog"][open], [data-state="open"][role="dialog"]');
        if (modal) {
          const closeBtn = modal.querySelector('[aria-label="Close"]');
          (closeBtn as HTMLButtonElement)?.click();
        }
        return;
      }

      if (e.key === "?" && !isInput) {
        e.preventDefault();
        return;
      }

      if (!isInput && e.key.length === 1) {
        keyBuffer += e.key.toLowerCase();
        if (bufferTimeout) clearTimeout(bufferTimeout);
        bufferTimeout = setTimeout(() => { keyBuffer = ""; }, 1000);

        const route = NAV_SHORTCUTS[keyBuffer];
        if (route) {
          e.preventDefault();
          navigate(route);
          keyBuffer = "";
          if (bufferTimeout) clearTimeout(bufferTimeout);
          bufferTimeout = null;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (bufferTimeout) clearTimeout(bufferTimeout);
    };
  }, [navigate, setSearchOpen]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const count = await getUnreadCount();
        setUnreadCount(count);
      } catch {
        // silently fail
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [setUnreadCount]);
}
