import { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import type { DayDetail } from "@fixly/shared-types";

const MOODS = [
  { value: "great", label: "Great", icon: "😄" },
  { value: "good", label: "Good", icon: "🙂" },
  { value: "okay", label: "Okay", icon: "😐" },
  { value: "bad", label: "Bad", icon: "😔" },
  { value: "terrible", label: "Terrible", icon: "😢" },
] as const;

interface StudyDiaryProps {
  day: DayDetail;
  onSave: (data: { mood?: string | null; productivity_rating?: number | null; notes?: string | null }) => void;
  onClose: () => void;
  isSaving?: boolean;
}

export function StudyDiary({ day, onSave, onClose, isSaving }: StudyDiaryProps) {
  const [mood, setMood] = useState<string | null>(day.mood);
  const [rating, setRating] = useState<number | null>(day.productivity_rating);
  const [notes, setNotes] = useState(day.notes || "");
  const [dirty, setDirty] = useState(false);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const prevDayDate = useRef(day.date);

  useEffect(() => {
    if (prevDayDate.current !== day.date) {
      setMood(day.mood);
      setRating(day.productivity_rating);
      setNotes(day.notes || "");
      setDirty(false);
      prevDayDate.current = day.date;
    }
  }, [day]);

  const scheduleAutoSave = useCallback(() => {
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    autoSaveTimer.current = setTimeout(() => {
      if (dirty) {
        onSave({ mood, productivity_rating: rating, notes: notes || null });
        setDirty(false);
      }
    }, 2000);
  }, [dirty, mood, rating, notes, onSave]);

  useEffect(() => {
    if (dirty) scheduleAutoSave();
    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, [dirty, scheduleAutoSave]);

  const handleMoodChange = (value: string) => {
    setMood(value);
    setDirty(true);
  };

  const handleRatingChange = (value: number) => {
    setRating(value);
    setDirty(true);
  };

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNotes(e.target.value);
    setDirty(true);
  };

  const handleSave = () => {
    onSave({ mood, productivity_rating: rating, notes: notes || null });
    setDirty(false);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatMinutes = (min: number) => {
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{formatDate(day.date)}</h3>
          <p className="text-sm text-muted-foreground">{day.study_points} points earned</p>
        </div>
        <div className="flex items-center gap-2">
          {dirty && <span className="text-xs text-muted-foreground">Unsaved changes</span>}
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
          <Button size="sm" onClick={handleSave} disabled={isSaving || !dirty}>
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <DiaryStat label="Study Time" value={formatMinutes(day.total_study_minutes)} />
        <DiaryStat label="Pomodoros" value={String(day.pomodoro_sessions)} />
        <DiaryStat label="Assignments" value={String(day.assignments_completed)} />
        <DiaryStat label="Subjects" value={day.subjects_studied.join(", ") || "None"} />
        <DiaryStat label="AI Chats" value={String(day.ai_conversations)} />
        <DiaryStat label="Points" value={String(day.study_points)} />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">How was your study day?</label>
        <div className="flex gap-2">
          {MOODS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => handleMoodChange(m.value)}
              className={`flex flex-col items-center gap-1 rounded-lg border px-3 py-2 text-sm transition-all ${
                mood === m.value
                  ? "border-primary bg-primary/10"
                  : "border-transparent hover:border-border"
              }`}
            >
              <span className="text-lg">{m.icon}</span>
              <span className="text-xs">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">
          Productivity Rating: {rating ? `${rating}/10` : "Not set"}
        </label>
        <div className="flex gap-1">
          {Array.from({ length: 10 }, (_, i) => i + 1).map((num) => (
            <button
              key={num}
              type="button"
              onClick={() => handleRatingChange(num)}
              className={`h-8 w-8 rounded-md text-xs font-medium transition-all ${
                rating === num
                  ? "bg-primary text-primary-foreground"
                  : rating !== null && num <= rating
                    ? "bg-primary/20 text-foreground"
                    : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Study Notes</label>
        <p className="text-xs text-muted-foreground">Supports Markdown</p>
        <textarea
          value={notes}
          onChange={handleNotesChange}
          rows={6}
          className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          placeholder="Write your study notes here... Use **bold**, *italic*, - lists, etc."
        />
      </div>
    </motion.div>
  );
}

function DiaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-sm font-medium truncate">{value}</p>
    </div>
  );
}
