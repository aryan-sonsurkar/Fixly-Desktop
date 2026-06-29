import { useEffect } from "react";
import { useSearchStore } from "@/stores/search-store";
import { useNotificationStore } from "@/stores/notification-store";
import { getUnreadCount } from "@/lib/notification-service";

export function useKeyboardShortcuts() {
  const { setOpen: setSearchOpen } = useSearchStore();
  const { setUnreadCount } = useNotificationStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setSearchOpen]);

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
