import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDebouncedValue } from "@/hooks/use-debounce";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@fixly/ui";
import {
  getAssignments,
  deleteAssignment,
  duplicateAssignment,
  getAssignmentStats,
  type AssignmentsQuery,
} from "@/lib/assignment-service";
import { getSubjects } from "@/lib/profile-service";
import { AssignmentCard } from "@/components/assignment-card";
import { AssignmentFormDialog } from "@/components/assignment-form-dialog";
import { AssignmentDetailDialog } from "@/components/assignment-detail-dialog";
import { DeleteConfirmDialog } from "@/components/delete-confirm-dialog";
import { FilterBar } from "@/components/filter-bar";
import { AssignmentEmptyState } from "@/components/assignment-empty-state";
import { AssignmentSkeleton } from "@/components/assignment-skeleton";
import { toast } from "@/stores/toast-store";
import { createLogger } from "@/lib/logger";
import type { Assignment } from "@fixly/shared-types";

const logger = createLogger("assignments-page");

export function AssignmentsPage() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState<AssignmentsQuery>({
    is_archived: false,
    sort_by: "due_date",
    sort_order: "asc",
    page: 1,
    page_size: 50,
  });
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  const debouncedQuery = useDebouncedValue(query, 300);
  const { data: assignmentsData, isLoading, isFetching, isError: isAssignmentsError, error: assignmentsError, refetch } = useQuery({
    queryKey: ["assignments", debouncedQuery],
    queryFn: () => getAssignments(debouncedQuery),
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    placeholderData: (prev) => prev,
  });

  const { data: stats, isError: isStatsError } = useQuery({
    queryKey: ["assignment-stats"],
    queryFn: getAssignmentStats,
    staleTime: 60 * 1000,
  });

  const { data: subjects, isError: isSubjectsError } = useQuery({
    queryKey: ["subjects"],
    queryFn: getSubjects,
    staleTime: 5 * 60 * 1000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["assignment-stats"] });
      setDeleteId(null);
      setDetailId(null);
      toast({ type: "info", title: "Assignment deleted" });
    },
    onError: (err) => {
      logger.error("Failed to delete assignment", err);
      setPageError("Failed to delete assignment. Please try again.");
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: string) => duplicateAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      toast({ type: "success", title: "Assignment duplicated" });
    },
    onError: (err) => {
      logger.error("Failed to duplicate assignment", err);
      setPageError("Failed to duplicate assignment. Please try again.");
    },
  });

  const subjectMap = new Map(subjects?.map((s) => [s.id, s]));

  const hasFilters = Object.entries(query).some(([k, v]) =>
    k !== "is_archived" && k !== "sort_by" && k !== "sort_order" && k !== "page" && k !== "page_size" && v
  );

  const showInitialSkeleton = isLoading && !assignmentsData;
  if (showInitialSkeleton) return <AssignmentSkeleton />;
  const isRefetching = isFetching && !!assignmentsData;

  if (isAssignmentsError && !assignmentsData) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <h2 className="text-lg font-semibold">Failed to load assignments</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {assignmentsError instanceof Error ? assignmentsError.message : "An unexpected error occurred"}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Assignments</h1>
          {stats && (
            <p className="text-sm text-muted-foreground">
              {stats.completed}/{stats.total} completed &middot; {stats.due_today} due today
            </p>
          )}
        </div>
        <Button onClick={() => { setEditingAssignment(null); setFormOpen(true); }}>
          + New Assignment
        </Button>
      </div>

      {(isStatsError || isSubjectsError) && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Some data failed to load.
        </div>
      )}

      {pageError && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {pageError}
        </div>
      )}

      <FilterBar query={query} onChange={setQuery} subjects={subjects || []} />

      {isRefetching && (
        <div className="h-1 w-full overflow-hidden rounded bg-muted">
          <div className="h-full w-1/2 animate-pulse bg-primary/50" />
        </div>
      )}

      {(!assignmentsData?.data || assignmentsData.data.length === 0) && !isAssignmentsError && (
        <AssignmentEmptyState
          hasFilters={hasFilters}
          onCreateNew={() => { setEditingAssignment(null); setFormOpen(true); }}
        />
      )}

      {assignmentsData && assignmentsData.data.length > 0 && (
        <div className="space-y-2">
          <AnimatePresence>
            {assignmentsData.data.map((assignment) => (
              <motion.div
                key={assignment.id}
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
              >
                <AssignmentCard
                  assignment={assignment}
                  subjectName={subjectMap.get(assignment.subject_id || "")?.name}
                  subjectColor={subjectMap.get(assignment.subject_id || "")?.color}
                  onClick={() => setDetailId(assignment.id)}
                  onEdit={() => { setEditingAssignment(assignment); setFormOpen(true); }}
                  onDelete={() => setDeleteId(assignment.id)}
                  onDuplicate={() => duplicateMutation.mutate(assignment.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <AssignmentFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        assignment={editingAssignment}
        subjects={subjects || []}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["assignments"] });
          queryClient.invalidateQueries({ queryKey: ["assignment-stats"] });
          setFormOpen(false);
          setEditingAssignment(null);
          toast({
            type: "success",
            title: editingAssignment ? "Assignment updated" : "Assignment created",
          });
        }}
      />

      <AssignmentDetailDialog
        assignmentId={detailId}
        onOpenChange={(open) => { if (!open) setDetailId(null); }}
        onEdit={(a) => { setDetailId(null); setEditingAssignment(a); setFormOpen(true); }}
      />

      <DeleteConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
