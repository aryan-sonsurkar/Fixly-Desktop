import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@fixly/ui";
import {
  getAssignments,
  deleteAssignment,
  duplicateAssignment,
  bulkAction,
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
import { createLogger } from "@/lib/logger";
import type { Assignment } from "@fixly/shared-types";

const logger = createLogger("assignments-page");

type ViewMode = "list" | "board";

const STATUS_COLUMNS = [
  { key: "pending", label: "Pending", color: "border-l-yellow-500" },
  { key: "in_progress", label: "In Progress", color: "border-l-blue-500" },
  { key: "completed", label: "Completed", color: "border-l-green-500" },
  { key: "overdue", label: "Overdue", color: "border-l-red-500" },
];

export function AssignmentsPage() {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [query, setQuery] = useState<AssignmentsQuery>({
    is_archived: false,
    sort_by: "created_at",
    sort_order: "desc",
    page: 1,
    page_size: 20,
  });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  const { data: assignmentsData, isLoading, isError: isAssignmentsError, error: assignmentsError } = useQuery({
    queryKey: ["assignments", query],
    queryFn: () => getAssignments(query),
  });

  const { data: stats, isError: isStatsError } = useQuery({
    queryKey: ["assignment-stats"],
    queryFn: getAssignmentStats,
  });

  const { data: subjects, isError: isSubjectsError } = useQuery({
    queryKey: ["subjects"],
    queryFn: getSubjects,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["assignment-stats"] });
      setDeleteId(null);
      setDetailId(null);
    },
    onError: (err) => {
      logger.error("Failed to delete assignment", err);
      setPageError("Failed to delete assignment. Please try again.");
    },
  });

  const bulkMutation = useMutation({
    mutationFn: ({ ids, action, value }: { ids: string[]; action: string; value?: string | boolean | null }) =>
      bulkAction(ids, action, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["assignment-stats"] });
      setSelectedIds(new Set());
    },
    onError: (err) => {
      logger.error("Failed to perform bulk action", err);
      setPageError("Failed to perform bulk action. Please try again.");
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: string) => duplicateAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
    onError: (err) => {
      logger.error("Failed to duplicate assignment", err);
      setPageError("Failed to duplicate assignment. Please try again.");
    },
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (!assignmentsData?.data) return;
    if (selectedIds.size === assignmentsData.data.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(assignmentsData.data.map((a) => a.id)));
    }
  };

  const assignmentsByStatus = (status: string) =>
    assignmentsData?.data?.filter((a) => a.status === status) || [];

  const subjectMap = new Map(subjects?.map((s) => [s.id, s]));

  const hasFilters = Object.entries(query).some(([k, v]) =>
    k !== "is_archived" && k !== "sort_by" && k !== "sort_order" && k !== "page" && k !== "page_size" && v
  );

  if (isLoading) return <AssignmentSkeleton />;

  if (isAssignmentsError && !assignmentsData) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <svg className="h-6 w-6 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-foreground">Failed to load assignments</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {assignmentsError instanceof Error ? assignmentsError.message : "An unexpected error occurred"}
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Reload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Assignments</h1>
          {stats && (
            <p className="text-sm text-muted-foreground">
              {stats.completed}/{stats.total} completed ({stats.completion_percentage}%) &middot;{" "}
              {stats.due_today} due today &middot; {stats.overdue} overdue
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex overflow-hidden rounded-lg border">
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`px-3 py-1.5 text-sm transition-colors ${viewMode === "list" ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
            >
              List
            </button>
            <button
              type="button"
              onClick={() => setViewMode("board")}
              className={`px-3 py-1.5 text-sm transition-colors ${viewMode === "board" ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
            >
              Board
            </button>
          </div>
          <Button onClick={() => { setEditingAssignment(null); setFormOpen(true); }}>
            + New Assignment
          </Button>
        </div>
      </div>

      {(isStatsError || isSubjectsError) && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Some data failed to load. Some features may be unavailable.
        </div>
      )}

      {pageError && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {pageError}
        </div>
      )}

      {selectedIds.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2"
        >
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <Button variant="outline" size="sm" onClick={() => bulkMutation.mutate({ ids: Array.from(selectedIds), action: "complete" })}>
            Complete
          </Button>
          <Button variant="outline" size="sm" onClick={() => bulkMutation.mutate({ ids: Array.from(selectedIds), action: "archive" })}>
            Archive
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSelectedIds(new Set())}>
            Clear
          </Button>
        </motion.div>
      )}

      <FilterBar
        query={query}
        onChange={setQuery}
        subjects={subjects || []}
      />

      {(!assignmentsData?.data || assignmentsData.data.length === 0) && !isAssignmentsError && (
        <AssignmentEmptyState
          hasFilters={hasFilters}
          onCreateNew={() => { setEditingAssignment(null); setFormOpen(true); }}
        />
      )}

      {viewMode === "list" && assignmentsData && assignmentsData.data.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-4 border-b pb-2 text-xs font-medium text-muted-foreground">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedIds.size === assignmentsData.data.length}
                onChange={toggleSelectAll}
                className="h-4 w-4 accent-primary"
              />
            </label>
            <span className="flex-1">Title</span>
            <span className="w-24">Subject</span>
            <span className="w-20">Priority</span>
            <span className="w-24">Status</span>
            <span className="w-28">Due Date</span>
          </div>
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
                  isSelected={selectedIds.has(assignment.id)}
                  onToggleSelect={() => toggleSelect(assignment.id)}
                  onClick={() => setDetailId(assignment.id)}
                  onEdit={() => { setEditingAssignment(assignment); setFormOpen(true); }}
                  onDelete={() => setDeleteId(assignment.id)}
                  onDuplicate={() => duplicateMutation.mutate(assignment.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {assignmentsData.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={query.page === 1}
                onClick={() => setQuery((q) => ({ ...q, page: (q.page || 1) - 1 }))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {assignmentsData.page} of {assignmentsData.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={query.page === assignmentsData.total_pages}
                onClick={() => setQuery((q) => ({ ...q, page: (q.page || 1) + 1 }))}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      )}

      {viewMode === "board" && assignmentsData && assignmentsData.data.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          {STATUS_COLUMNS.map((col) => {
            const items = assignmentsByStatus(col.key);
            return (
              <div key={col.key} className="rounded-lg border bg-muted/30 p-3">
                <h3 className="mb-3 text-sm font-semibold text-muted-foreground">
                  {col.label} ({items.length})
                </h3>
                <div className="space-y-2">
                  {items.map((assignment) => (
                    <motion.div
                      key={assignment.id}
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className={`cursor-pointer rounded-lg border-l-4 bg-card p-3 shadow-sm hover:shadow-md transition-shadow ${
                        assignment.priority === "urgent" ? "border-l-red-500" :
                        assignment.priority === "high" ? "border-l-orange-500" :
                        assignment.priority === "medium" ? "border-l-blue-500" : "border-l-gray-400"
                      }`}
                      onClick={() => setDetailId(assignment.id)}
                    >
                      <p className="text-sm font-medium truncate">{assignment.title}</p>
                      {assignment.due_date && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Due: {new Date(assignment.due_date).toLocaleDateString()}
                        </p>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            );
          })}
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
