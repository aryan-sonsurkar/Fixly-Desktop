import { useEffect, useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Input, Label, Skeleton } from "@fixly/ui";
import { getSubjects, createSubject, updateSubject, deleteSubject } from "@/lib/profile-service";
import { toast } from "@/stores/toast-store";
import { createLogger } from "@/lib/logger";
import type { Subject } from "@fixly/shared-types";

const logger = createLogger("subjects-page");

const SUBJECT_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
  "#06b6d4", "#d946ef", "#e11d48", "#0ea5e9", "#65a30d",
];

const subjectFormSchema = z.object({
  name: z.string().min(1, "Subject name is required").max(100),
  credits: z.coerce.number().min(0).max(30).optional(),
});

type SubjectForm = z.infer<typeof subjectFormSchema>;

export function SubjectsPage() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState(SUBJECT_COLORS[0]);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const form = useForm<SubjectForm>({
    resolver: zodResolver(subjectFormSchema),
    defaultValues: { name: "", credits: undefined },
  });

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const { data: subjects = [], isLoading: loading, isFetching, isError: loadError, error: queryError, refetch } = useQuery({
    queryKey: ["subjects"],
    queryFn: getSubjects,
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    placeholderData: (prev) => prev,
  });
  const loadErrorMsg = loadError ? (queryError instanceof Error ? queryError.message : "Failed to load subjects. Please try again.") : null;

  const createMut = useMutation({
    mutationFn: (vars: { name: string; color: string; credits?: number }) => createSubject(vars),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ["subjects"] });
      form.reset({ name: "", credits: undefined });
      setSelectedColor(SUBJECT_COLORS[0]);
      toast({ type: "success", title: "Subject created", message: vars.name });
    },
    onError: (err) => { logger.error("Failed to create subject", err); setError("Failed to create subject. Please try again."); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, vars }: { id: string; vars: { name: string; color: string; credits?: number } }) => updateSubject(id, vars),
    onSuccess: (_data, { vars }) => {
      queryClient.invalidateQueries({ queryKey: ["subjects"] });
      setEditingId(null);
      form.reset({ name: "", credits: undefined });
      setSelectedColor(SUBJECT_COLORS[0]);
      toast({ type: "success", title: "Subject updated", message: vars.name });
    },
    onError: (err) => { logger.error("Failed to update subject", err); setError("Failed to update subject. Please try again."); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteSubject(id),
    onSuccess: (_data, id) => {
      const del = subjects.find((s) => s.id === id);
      queryClient.invalidateQueries({ queryKey: ["subjects"] });
      if (del) toast({ type: "info", title: "Subject deleted", message: del.name });
    },
    onError: (err) => { logger.error("Failed to delete subject", err); setError("Failed to delete subject. Please try again."); },
  });
  const submitting = createMut.isPending || updateMut.isPending || deleteMut.isPending;

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);
  const loadSubjects = () => refetch();

  const handleCreate = form.handleSubmit(async (data) => {
    setError(null);
    createMut.mutate({ name: data.name, color: selectedColor, credits: data.credits ?? undefined });
  });
  const handleUpdate = form.handleSubmit(async (data) => {
    if (!editingId) return;
    setError(null);
    updateMut.mutate({ id: editingId, vars: { name: data.name.trim(), color: selectedColor, credits: data.credits ?? undefined } });
  });
  const handleDelete = async (id: string) => {
    setError(null);
    deleteMut.mutate(id);
  };

  const startEdit = (subject: Subject) => {
    setEditingId(subject.id);
    setError(null);
    form.setValue("name", subject.name);
    form.setValue("credits", subject.credits ?? undefined);
    setSelectedColor(subject.color || SUBJECT_COLORS[0]);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setError(null);
    form.reset({ name: "", credits: undefined });
    setSelectedColor(SUBJECT_COLORS[0]);
  };

  if (loading && subjects.length === 0) {
    return (
      <div className="mx-auto max-w-2xl space-y-8 p-6 animate-in fade-in duration-100">
        <Skeleton className="h-8 w-32 animate-pulse" />
        <Skeleton className="h-4 w-56 animate-pulse" />
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-10 w-full animate-pulse" />
          <Skeleton className="h-10 w-24 animate-pulse" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }
  if (loadErrorMsg) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <p className="text-sm text-destructive mb-4">{loadErrorMsg}</p>
          <Button onClick={() => refetch()} variant="outline" size="sm">Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold">Subjects</h1>
        <p className="text-sm text-muted-foreground">Manage your academic subjects</p>
      </div>

      {error && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
      )}

      <div className="rounded-lg border p-6">
        <h2 className="mb-4 text-lg font-semibold">
          {editingId ? "Edit Subject" : "Add Subject"}
        </h2>
        <form onSubmit={editingId ? handleUpdate : handleCreate} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Subject Name</Label>
            <Input id="name" placeholder="e.g. Mathematics" autoFocus {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Color</Label>
            <div className="flex flex-wrap gap-2">
              {SUBJECT_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setSelectedColor(c)}
                  className={`h-8 w-8 rounded-full transition-transform ${selectedColor === c ? "scale-125 ring-2 ring-ring ring-offset-2" : ""}`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="credits">Credits <span className="text-muted-foreground">(optional)</span></Label>
            <Input id="credits" type="number" min={0} max={30} placeholder="4" {...form.register("credits")} />
          </div>

          <div className="flex gap-3">
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : editingId ? "Update" : "Add Subject"}
            </Button>
            {editingId && (
              <Button type="button" variant="outline" onClick={cancelEdit} disabled={submitting}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </div>

      <div className="space-y-3">
        <AnimatePresence>
          {subjects.map((subject) => (
            <motion.div
              key={subject.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-4 rounded-lg border px-5 py-4"
            >
              <div className="h-4 w-4 rounded-full" style={{ backgroundColor: subject.color || "#3b82f6" }} />
              <div className="flex-1">
                <p className="font-medium">{subject.name}</p>
                {subject.credits != null && (
                  <p className="text-xs text-muted-foreground">{subject.credits} credits</p>
                )}
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => startEdit(subject)} disabled={submitting}>
                Edit
              </Button>
              <Button type="button" variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={() => handleDelete(subject.id)} disabled={submitting}>
                Delete
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>

        {subjects.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center py-12 text-center"
          >
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <svg className="h-8 w-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="mb-1 text-lg font-medium">No subjects yet</h3>
            <p className="text-sm text-muted-foreground">Add your first subject above to get started organizing your coursework.</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
