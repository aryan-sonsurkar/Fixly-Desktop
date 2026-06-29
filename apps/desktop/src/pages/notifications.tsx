import { useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";
import { useNotificationStore } from "@/stores/notification-store";
import { getNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead, deleteNotification } from "@/lib/notification-service";

const typeIcons: Record<string, string> = {
  assignment_reminder: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  deadline_alert: "M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z",
  exam_reminder: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
  daily_briefing: "M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z",
  pomodoro_finished: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  email_sync: "M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75",
  ocr_completed: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
  ai_recommendation: "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z",
};

const typeColors: Record<string, string> = {
  assignment_reminder: "text-blue-500 bg-blue-500/10",
  deadline_alert: "text-red-500 bg-red-500/10",
  exam_reminder: "text-orange-500 bg-orange-500/10",
  daily_briefing: "text-purple-500 bg-purple-500/10",
  pomodoro_finished: "text-green-500 bg-green-500/10",
  email_sync: "text-cyan-500 bg-cyan-500/10",
  ocr_completed: "text-indigo-500 bg-indigo-500/10",
  ai_recommendation: "text-yellow-500 bg-yellow-500/10",
};

const filterTypes = [
  { value: null, label: "All" },
  { value: "assignment_reminder", label: "Assignments" },
  { value: "exam_reminder", label: "Exams" },
  { value: "deadline_alert", label: "Deadlines" },
  { value: "email_sync", label: "Email" },
  { value: "ai_recommendation", label: "AI" },
  { value: "daily_briefing", label: "Briefing" },
];

function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return "Just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function NotificationPage() {
  const {
    notifications, total, page, unreadCount, loading, filterType, filterUnread,
    setNotifications, addNotifications, setTotal, setPage, setUnreadCount, setLoading,
    setFilterType, setFilterUnread, markRead, markAllRead: markAllInStore, removeNotification,
  } = useNotificationStore();

  const loaderRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async (pageNum: number, append: boolean = false) => {
    setLoading(true);
    try {
      const data = await getNotifications({
        unread_only: filterUnread,
        type: filterType || undefined,
        page: pageNum,
        page_size: 20,
      });
      if (append) {
        addNotifications(data.notifications);
      } else {
        setNotifications(data.notifications);
      }
      setTotal(data.total);
      setPage(pageNum);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [filterType, filterUnread, setNotifications, addNotifications, setTotal, setPage, setLoading]);

  useEffect(() => {
    fetchNotifications(1);
    getUnreadCount().then(setUnreadCount).catch(() => {});
  }, [filterType, filterUnread]);

  useEffect(() => {
    if (page > 1) fetchNotifications(page, true);
  }, [page]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && notifications.length < total) {
          setPage(page + 1);
        }
      },
      { threshold: 0.1 },
    );
    if (loaderRef.current) observer.observe(loaderRef.current);
    return () => observer.disconnect();
  }, [loading, notifications.length, total, page, setPage]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      markRead(id);
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch {
      // silently fail
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      markAllInStore();
      setUnreadCount(0);
    } catch {
      // silently fail
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotification(id);
      removeNotification(id);
      setTotal(Math.max(0, total - 1));
    } catch {
      // silently fail
    }
  };

  const unreadNotifications = notifications.filter((n) => !n.is_read);

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          <p className="text-sm text-muted-foreground">
            {unreadCount > 0 ? `${unreadCount} unread` : "All caught up!"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            Mark all read
          </Button>
        )}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setFilterUnread(!filterUnread)}
          className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
            filterUnread ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
          }`}
        >
          Unread only
        </button>
        {filterTypes.map((ft) => (
          <button
            key={ft.label}
            type="button"
            onClick={() => setFilterType(ft.value)}
            className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
              filterType === ft.value ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
            }`}
          >
            {ft.label}
          </button>
        ))}
      </div>

      <div className="space-y-1">
        {notifications.length === 0 && !loading && (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <p className="text-sm text-muted-foreground">No notifications</p>
          </div>
        )}

        <AnimatePresence>
          {unreadNotifications.map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onMarkRead={handleMarkRead}
              onDelete={handleDelete}
            />
          ))}
          {notifications.filter((n) => n.is_read).map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onMarkRead={handleMarkRead}
              onDelete={handleDelete}
            />
          ))}
        </AnimatePresence>

        {loading && (
          <div className="space-y-2 py-4">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}
          </div>
        )}

        {notifications.length < total && !loading && (
          <div ref={loaderRef} className="py-4 text-center text-xs text-muted-foreground">
            Scroll for more
          </div>
        )}
      </div>
    </div>
  );
}

function NotificationItem({
  notification: n,
  onMarkRead,
  onDelete,
}: {
  notification: { id: string; type: string; title: string; message: string; is_read: boolean; created_at: string };
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 8, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.2 }}
      className={`group flex items-start gap-3 rounded-lg p-4 text-sm transition-colors ${
        !n.is_read ? "border-l-2 border-l-primary bg-card" : "hover:bg-accent/50"
      }`}
    >
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${typeColors[n.type] || "bg-muted text-muted-foreground"}`}>
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d={typeIcons[n.type] || "M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"} />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          {!n.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />}
          <p className={`truncate ${!n.is_read ? "font-medium" : ""}`}>{n.title}</p>
        </div>
        {n.message && (
          <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{n.message}</p>
        )}
        <p className="mt-1 text-[10px] text-muted-foreground">{formatTime(n.created_at)}</p>
      </div>
      <div className="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        {!n.is_read && (
          <button
            type="button"
            onClick={() => onMarkRead(n.id)}
            className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
            title="Mark read"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </button>
        )}
        <button
          type="button"
          onClick={() => onDelete(n.id)}
          className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          title="Delete"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </motion.div>
  );
}
