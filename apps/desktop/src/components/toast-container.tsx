import { motion, AnimatePresence } from "framer-motion";
import { useToastStore } from "@/stores/toast-store";

const typeStyles: Record<string, { bg: string; icon: string; border: string }> = {
  success: {
    bg: "bg-green-500/10",
    icon: "M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    border: "border-green-500/30",
  },
  error: {
    bg: "bg-red-500/10",
    icon: "M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z",
    border: "border-red-500/30",
  },
  info: {
    bg: "bg-blue-500/10",
    icon: "M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z",
    border: "border-blue-500/30",
  },
  warning: {
    bg: "bg-yellow-500/10",
    icon: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
    border: "border-yellow-500/30",
  },
};

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2" aria-live="polite" aria-label="Notifications">
      <AnimatePresence>
        {toasts.map((t) => {
          const style = typeStyles[t.type];
          setTimeout(() => removeToast(t.id), t.duration || 4000);
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 80, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.9 }}
              className={`flex items-start gap-3 rounded-lg border ${style.border} ${style.bg} bg-card px-4 py-3 shadow-lg backdrop-blur-sm max-w-sm`}
            >
              <svg className="h-5 w-5 shrink-0 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
              </svg>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{t.title}</p>
                {t.message && <p className="text-xs text-muted-foreground">{t.message}</p>}
              </div>
              <button
                type="button"
                onClick={() => removeToast(t.id)}
                className="shrink-0 rounded p-0.5 text-muted-foreground hover:bg-accent"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
