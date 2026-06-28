import { useState, useCallback, useRef } from "react";
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
import { createLogger } from "@/lib/logger";
import { AssignmentCard } from "@/components/assignment-card";
import { AssignmentFormDialog } from "@/components/assignment-form-dialog";
import { AssignmentDetailDialog } from "@/components/assignment-detail-dialog";
import { DeleteConfirmDialog } from "@/components/delete-confirm-dialog";
import { FilterBar } from "@/components/filter-bar";
import { AssignmentEmptyState } from "@/components/assignment-empty-state";
import { AssignmentSkeleton } from "@/components/assignment-skeleton";
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

  const { data: assignmentsData, isLoading } = useQuery({
    queryKey: ["assignments", query],
    queryFn: () => getAssignments(query),
  });

  const { data: stats } = useQuery({
    queryKey: ["assignment-stats"],
    queryFn: getAssignmentStats,
  });

  const { data: subjects } = useQuery({
    queryKey: ["subjects"],
    queryFn: getSubjects,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["assignment-stats"] });
      setDeleteId(null);
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
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: string) => duplicateAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
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

  if (isLoading) return <AssignmentSkeleton />;

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

      {(!assignmentsData?.data || assignmentsData.data.length === 0) && (
        <AssignmentEmptyState
          hasFilters={Object.entries(query).some(([k, v]) =>
            k !== "is_archived" && k !== "sort_by" && k !== "sort_order" && k !== "page" && k !== "page_size" && v
          )}
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

      {viewMode === "board" && (
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
