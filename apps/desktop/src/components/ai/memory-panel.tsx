import { useState, useEffect, useCallback } from "react";
import {
  Button,
  Badge,
  Card,
  CardContent,
  Input,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@fixly/ui";
import {
  listMemories,
  updateMemory,
  deleteMemory,
  archiveMemory,
  resetAllMemories,
  type Memory,
} from "@/lib/memory-service";

const CATEGORY_LABELS: Record<string, string> = {
  fact: "Fact",
  preference: "Preference",
  habit: "Habit",
  weakness: "Weakness",
  strength: "Strength",
  goal: "Goal",
  document: "Document",
};

const CATEGORY_COLORS: Record<string, string> = {
  fact: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  preference:
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  habit: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  weakness:
    "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  strength:
    "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  goal: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300",
  document:
    "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
};

function confidenceLabel(c: number): string {
  if (c >= 0.7) return "High";
  if (c >= 0.4) return "Medium";
  return "Low";
}

function sourceLabel(s: string): string {
  const map: Record<string, string> = {
    explicit: "Direct statement",
    inferred: "Inferred",
    behavioral: "Observed behavior",
    conversation: "Conversation",
    document: "Document",
  };
  return map[s] || s;
}

interface MemoryPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MemoryPanel({ open, onOpenChange }: MemoryPanelProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const loadMemories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listMemories({
        category: categoryFilter || undefined,
      });
      setMemories(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [categoryFilter]);

  useEffect(() => {
    if (open) loadMemories();
  }, [open, loadMemories]);

  const filtered = memories.filter(
    (m) =>
      !m.is_archived &&
      (filter === "" || m.content.toLowerCase().includes(filter.toLowerCase()))
  );

  const handleSave = async (id: string) => {
    try {
      await updateMemory(id, { content: editContent });
      setEditingId(null);
      loadMemories();
    } catch {
      // silently fail
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      loadMemories();
    } catch {
      // silently fail
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await archiveMemory(id);
      loadMemories();
    } catch {
      // silently fail
    }
  };

  const handleReset = async () => {
    try {
      await resetAllMemories();
      setMemories([]);
      setShowResetConfirm(false);
    } catch {
      // silently fail
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Fixly Memory</DialogTitle>
          <DialogDescription>
            Things Fixly remembers about you from conversations and documents.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 items-center">
          <Input
            placeholder="Search memories..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="flex-1"
          />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="h-9 rounded-md border bg-background px-3 text-sm"
          >
            <option value="">All categories</option>
            {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
          {loading ? (
            <div className="text-center text-muted-foreground py-8">
              Loading memories...
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              {filter
                ? "No memories match your search."
                : "Fixly doesn't have any memories yet. They'll appear as you chat."}
            </div>
          ) : (
            filtered.map((memory) => (
              <Card key={memory.id} className="relative">
                <CardContent className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      {editingId === memory.id ? (
                        <div className="space-y-2">
                          <Input
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="text-sm"
                          />
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => handleSave(memory.id)}
                            >
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setEditingId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <p className="text-sm font-medium leading-relaxed">
                            &ldquo;{memory.content}&rdquo;
                          </p>
                          <div className="flex flex-wrap gap-1.5 mt-1.5">
                            <Badge
                              variant="secondary"
                              className={`text-xs ${CATEGORY_COLORS[memory.category] || ""}`}
                            >
                              {CATEGORY_LABELS[memory.category] || memory.category}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {confidenceLabel(memory.confidence)} confidence
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {sourceLabel(memory.source)}
                            </Badge>
                          </div>
                        </>
                      )}
                    </div>
                    {editingId !== memory.id && (
                      <div className="flex gap-0.5 shrink-0">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-xs"
                          onClick={() => {
                            setEditingId(memory.id);
                            setEditContent(memory.content);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-xs"
                          onClick={() => handleArchive(memory.id)}
                        >
                          Archive
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-xs text-destructive"
                          onClick={() => handleDelete(memory.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <Separator />

        <DialogFooter className="flex-row justify-between">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowResetConfirm(true)}
          >
            Reset All Memories
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>

        <Dialog open={showResetConfirm} onOpenChange={setShowResetConfirm}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reset All Memories?</DialogTitle>
              <DialogDescription>
                This will permanently delete all AI memories, conversation
                history, and learned preferences. This cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="ghost"
                onClick={() => setShowResetConfirm(false)}
              >
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleReset}>
                Reset Everything
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  );
}
