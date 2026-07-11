import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@fixly/ui";
import { submitFeedback } from "@/lib/feedback-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("feedback");

type Tab = "bug" | "feature" | "rating";

const emojis = [
  { value: 1, label: "Terrible", icon: "M12 9c-1.5 0-2.5-.5-3-1m3 1c1.5 0 2.5-.5 3-1m-3 1v3m-3 3c1-.5 2-1 3-1s2 .5 3 1" },
  { value: 2, label: "Poor", icon: "M12 9c-1 0-2-.5-2.5-1m2.5 1c1 0 2-.5 2.5-1M12 12v2m-4 0c1.5-.5 3-.5 4 0s2.5.5 4 0" },
  { value: 3, label: "Okay", icon: "M12 9c1 0 2-.5 2-1m-2 1c-1 0-2-.5-2-1m4 4c-1.5.5-3 .5-4 0s-2.5-.5-4 0" },
  { value: 4, label: "Good", icon: "M12 9c1 0 2-.5 2-1m-2 1c-1 0-2-.5-2-1m2 4c1.5.5 3 .5 4 0m-8 0c-1.5.5-3 .5-4 0" },
  { value: 5, label: "Amazing", icon: "M12 9c1.5 0 2.5-.5 3-1m-3 1c-1.5 0-2.5-.5-3-1m0 4c1 .5 2 1 3 1s2-.5 3-1" },
];

export function FeedbackDialog() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("bug");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rating, setRating] = useState(0);
  const [attachLogs, setAttachLogs] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [hoverRating, setHoverRating] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    setSubmitting(true);
    try {
      await submitFeedback({
        type: tab,
        title: tab !== "rating" ? title : undefined,
        description: description.trim(),
        rating: tab === "rating" ? rating : undefined,
        attach_logs: attachLogs,
      });
      setSubmitted(true);
      setTimeout(() => {
        setOpen(false);
        setSubmitted(false);
        setTitle("");
        setDescription("");
        setRating(0);
      }, 2000);
    } catch (err) {
      logger.error("Failed to submit feedback", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-110 hover:shadow-xl active:scale-95"
        aria-label="Send feedback"
        title="Send feedback"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-lg rounded-2xl border bg-card p-6 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-label="Send feedback"
            >
              {submitted ? (
                <div className="flex flex-col items-center gap-3 py-8 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success/10">
                    <svg className="h-6 w-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold">Thank you!</h3>
                  <p className="text-sm text-muted-foreground">Your feedback helps make Fixly better.</p>
                </div>
              ) : (
                <>
                  <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Send Feedback</h2>
                    <button
                      type="button"
                      onClick={() => setOpen(false)}
                      className="rounded-lg p-1 text-muted-foreground hover:bg-muted"
                      aria-label="Close"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  <div className="mb-6 flex rounded-lg border p-1">
                    {(["bug", "feature", "rating"] as Tab[]).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setTab(t)}
                        className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                          tab === t ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {t === "bug" ? "Bug Report" : t === "feature" ? "Feature Request" : "Rate Experience"}
                      </button>
                    ))}
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    {tab !== "rating" && (
                      <div className="space-y-2">
                        <label htmlFor="feedback-title" className="text-sm font-medium">Title</label>
                        <input
                          id="feedback-title"
                          type="text"
                          value={title}
                          onChange={(e) => setTitle(e.target.value)}
                          placeholder={tab === "bug" ? "Brief description of the bug" : "Brief description of your idea"}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        />
                      </div>
                    )}

                    <div className="space-y-2">
                      <label htmlFor="feedback-desc" className="text-sm font-medium">
                        {tab === "rating" ? "Your thoughts" : "Description"}
                      </label>
                      <textarea
                        id="feedback-desc"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={4}
                        placeholder={
                          tab === "bug" ? "What happened? What did you expect?" :
                          tab === "feature" ? "What would you like to see?" :
                          "Tell us what you think about Fixly..."
                        }
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
                        required
                      />
                    </div>

                    {tab === "rating" && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Rating</p>
                        <div className="flex justify-center gap-2">
                          {emojis.map((e) => {
                            const active = (hoverRating || rating) >= e.value;
                            return (
                              <button
                                key={e.value}
                                type="button"
                                onClick={() => setRating(e.value)}
                                onMouseEnter={() => setHoverRating(e.value)}
                                onMouseLeave={() => setHoverRating(0)}
                                className={`flex flex-col items-center gap-1 rounded-lg p-2 transition-all ${
                                  active ? "scale-110" : "opacity-50 hover:opacity-80"
                                }`}
                                title={e.label}
                              >
                                <svg className={`h-8 w-8 ${active ? "text-yellow-500" : "text-muted-foreground"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d={e.icon} />
                                </svg>
                                <span className="text-[10px] text-muted-foreground">{e.label}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    <label className="flex cursor-pointer items-center gap-2 rounded-lg border p-3">
                      <input
                        type="checkbox"
                        checked={attachLogs}
                        onChange={(e) => setAttachLogs(e.target.checked)}
                        className="h-4 w-4 accent-primary"
                      />
                      <div>
                        <p className="text-sm font-medium">Attach diagnostics</p>
                        <p className="text-xs text-muted-foreground">Includes app version, recent activity, and errors. No personal data.</p>
                      </div>
                    </label>

                    <div className="flex justify-end gap-3 pt-2">
                      <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={submitting || !description.trim() || (tab === "rating" && rating === 0)}>
                        {submitting ? "Sending..." : "Send Feedback"}
                      </Button>
                    </div>
                  </form>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
