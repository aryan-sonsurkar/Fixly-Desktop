import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button, Input, Label } from "@fixly/ui";
import { createAssignment, updateAssignment } from "@/lib/assignment-service";
import { createLogger } from "@/lib/logger";
import type { Assignment } from "@fixly/shared-types";
import type { Subject } from "@fixly/shared-types";

const logger = createLogger("assignment-form-dialog");

const assignmentSchema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().optional(),
  subject_id: z.string().optional(),
  priority: z.enum(["low", "medium", "high", "urgent"]),
  status: z.enum(["pending", "in_progress", "completed", "overdue"]),
  due_date: z.string().optional(),
  estimated_study_time: z.coerce.number().min(1).max(1440).optional(),
  tags: z.string().optional(),
  notes: z.string().optional(),
  is_pinned: z.boolean().optional(),
  is_favorite: z.boolean().optional(),
});

type AssignmentForm = z.infer<typeof assignmentSchema>;

interface AssignmentFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assignment: Assignment | null;
  subjects: Subject[];
  onSuccess: () => void;
}

export function AssignmentFormDialog({
  open,
  onOpenChange,
  assignment,
  subjects,
  onSuccess,
}: AssignmentFormDialogProps) {
  const isEditing = !!assignment;

  const form = useForm<AssignmentForm>({
    resolver: zodResolver(assignmentSchema),
    defaultValues: {
      title: "",
      description: "",
      subject_id: "",
      priority: "medium",
      status: "pending",
      due_date: "",
      estimated_study_time: undefined,
      tags: "",
      notes: "",
      is_pinned: false,
      is_favorite: false,
    },
  });

  useEffect(() => {
    if (assignment) {
      form.reset({
        title: assignment.title,
        description: assignment.description || "",
        subject_id: assignment.subject_id || "",
        priority: assignment.priority as "low" | "medium" | "high" | "urgent",
        status: assignment.status as "pending" | "in_progress" | "completed" | "overdue",
        due_date: assignment.due_date ? assignment.due_date.slice(0, 16) : "",
        estimated_study_time: assignment.estimated_study_time || undefined,
        tags: assignment.tags?.join(", ") || "",
        notes: assignment.notes || "",
        is_pinned: assignment.is_pinned,
        is_favorite: assignment.is_favorite,
      });
    } else {
      form.reset({
        title: "",
        description: "",
        subject_id: "",
        priority: "medium",
        status: "pending",
        due_date: "",
        estimated_study_time: undefined,
        tags: "",
        notes: "",
        is_pinned: false,
        is_favorite: false,
      });
    }
  }, [assignment, form]);

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      const payload = {
        title: data.title,
        description: data.description || null,
        subject_id: data.subject_id || null,
        priority: data.priority,
        status: data.status,
        due_date: data.due_date ? new Date(data.due_date).toISOString() : null,
        estimated_study_time: data.estimated_study_time || null,
        tags: data.tags ? data.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
        notes: data.notes || null,
        is_pinned: data.is_pinned || false,
        is_favorite: data.is_favorite || false,
      };

      if (isEditing) {
        await updateAssignment(assignment.id, payload);
      } else {
        await createAssignment(payload);
      }
      onSuccess();
    } catch (err) {
      logger.error("Failed to save assignment", err);
    }
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => onOpenChange(false)}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold">{isEditing ? "Edit Assignment" : "New Assignment"}</h2>
          <button type="button" onClick={() => onOpenChange(false)} className="text-muted-foreground hover:text-foreground">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" placeholder="Assignment title" autoFocus {...form.register("title")} />
            {form.formState.errors.title && (
              <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <textarea
              id="description"
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Description (optional)"
              {...form.register("description")}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="subject_id">Subject</Label>
              <select
                id="subject_id"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                {...form.register("subject_id")}
              >
                <option value="">No subject</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <select id="priority" className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" {...form.register("priority")}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Critical</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select id="status" className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" {...form.register("status")}>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="due_date">Due Date</Label>
              <Input id="due_date" type="datetime-local" {...form.register("due_date")} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="estimated_study_time">Est. Time (min)</Label>
              <Input id="estimated_study_time" type="number" min={1} max={1440} placeholder="60" {...form.register("estimated_study_time")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <Input id="tags" placeholder="exam, quiz, project" {...form.register("tags")} />
              <p className="text-xs text-muted-foreground">Comma-separated</p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              rows={2}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Notes (optional)"
              {...form.register("notes")}
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input type="checkbox" {...form.register("is_pinned")} className="h-4 w-4 accent-primary" />
              Pin
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input type="checkbox" {...form.register("is_favorite")} className="h-4 w-4 accent-primary" />
              Favorite
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Saving..." : isEditing ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
