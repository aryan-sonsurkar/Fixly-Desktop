import { create } from "zustand";
import type { NotificationItem } from "@/lib/notification-service";

export interface NotificationState {
  notifications: NotificationItem[];
  total: number;
  page: number;
  unreadCount: number;
  loading: boolean;
  error: string | null;
  filterType: string | null;
  filterUnread: boolean;
  setNotifications: (notifications: NotificationItem[]) => void;
  addNotifications: (notifications: NotificationItem[]) => void;
  setTotal: (total: number) => void;
  setPage: (page: number) => void;
  setUnreadCount: (count: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilterType: (type: string | null) => void;
  setFilterUnread: (unread: boolean) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  removeNotification: (id: string) => void;
  reset: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  total: 0,
  page: 1,
  unreadCount: 0,
  loading: false,
  error: null,
  filterType: null,
  filterUnread: false,

  setNotifications: (notifications) => set({ notifications }),
  addNotifications: (notifications) =>
    set((state) => ({
      notifications: [...state.notifications, ...notifications],
    })),
  setTotal: (total) => set({ total }),
  setPage: (page) => set({ page }),
  setUnreadCount: (count) => set({ unreadCount: count }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilterType: (type) => set({ filterType: type, page: 1 }),
  setFilterUnread: (unread) => set({ filterUnread: unread, page: 1 }),
  markRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n,
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),
  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      total: Math.max(0, state.total - 1),
    })),
  reset: () =>
    set({
      notifications: [],
      total: 0,
      page: 1,
      unreadCount: 0,
      loading: false,
      filterType: null,
      filterUnread: false,
    }),
}));
