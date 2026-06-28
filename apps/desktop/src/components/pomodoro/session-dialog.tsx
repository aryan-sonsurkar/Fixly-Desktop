import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button, Input, Label } from "@fixly/ui";

interface SessionDialogProps {
  open: boolean;
  cyclesCompleted: number;
  onSubmit: (data: {
    interruptions: number;
    notes: string;
    mood_after: string;
    tags: string[];
  }) => void;
  onClose: () => void;
}

const moods = [
  { value: "great", label: "Great", emoji: "\u{1F929}" },
  { value: "good", label: "Good", emoji: "\u{1F60A}" },
  { value: "okay", label: "Okay", emoji: "\u{1F610}" },
  { value: "bad", label: "Bad", emoji: "\u{1F61E}" },
  { value: "terrible", label: "Terrible", emoji: "\u{1F622}" },
];

export function SessionDialog({ open, cyclesCompleted, onSubmit, onClose }: SessionDialogProps) {
  const [interruptions, setInterruptions] = useState(0);
  const [notes, setNotes] = useState("");
  const [mood, setMood] = useState("good");
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  const handleAddTag = () => {
    const t = tagInput.trim();
    if (t && !tags.includes(t)) {
      setTags([...tags, t]);
      setTagInput("");
    }
  };

  const handleSubmit = () => {
    onSubmit({ interruptions, notes, mood_after: mood, tags });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Session Complete!</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            You completed {cyclesCompleted} cycle{cyclesCompleted !== 1 ? "s" : ""}. How did it go?
          </p>

          <div className="space-y-1.5">
            <Label>How are you feeling?</Label>
            <div className="flex gap-2">
              {moods.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setMood(m.value)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-3 py-2 text-sm transition-colors ${
                    mood === m.value
                      ? "border-primary bg-primary/10"
                      : "hover:bg-accent"
                  }`}
                >
                  <span className="text-lg">{m.emoji}</span>
                  <span className="text-xs">{m.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Interruptions</Label>
            <Input
              type="number" min={0}
              value={interruptions}
              onChange={(e) => setInterruptions(Number(e.target.value))}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Tags</Label>
            <div className="flex gap-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
                placeholder="Add a tag..."
              />
              <Button variant="outline" onClick={handleAddTag}>Add</Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {tags.map((t) => (
                  <span key={t} className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs">
                    {t}
                    <button type="button" onClick={() => setTags(tags.filter((x) => x !== t))} className="text-muted-foreground hover:text-foreground">&times;</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Notes</Label>
            <textarea
              className="min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm resize-none"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What did you work on?"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Skip</Button>
          <Button onClick={handleSubmit}>Save Session</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
