import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import { getAssignment, getAssignmentAttachments, uploadAttachment, deleteAttachment } from "@/lib/assignment-service";
import type { Assignment } from "@fixly/shared-types";


interface AssignmentDetailDialogProps {
  assignmentId: string | null;
  onOpenChange: (open: boolean) => void;
  onEdit: (assignment: Assignment) => void;
}

export function AssignmentDetailDialog({
  assignmentId,
  onOpenChange,
  onEdit,
}: AssignmentDetailDialogProps) {
  const queryClient = useQueryClient();
  const open = !!assignmentId;

  const { data: assignment, isLoading } = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => getAssignment(assignmentId!),
    enabled: !!assignmentId,
  });

  const { data: attachments } = useQuery({
    queryKey: ["attachments", assignmentId],
    queryFn: () => getAssignmentAttachments(assignmentId!),
    enabled: !!assignmentId,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!assignmentId) throw new Error("No assignment ID");
      return uploadAttachment(assignmentId, file);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attachments", assignmentId] });
    },
  });

  const deleteAttachmentMutation = useMutation({
    mutationFn: (id: string) => deleteAttachment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attachments", assignmentId] });
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => onOpenChange(false)}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold">{assignment?.title || "Assignment"}</h2>
          <button type="button" onClick={() => onOpenChange(false)} className="text-muted-foreground hover:text-foreground">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : assignment ? (
          <div className="space-y-6">
            <div className="flex flex-wrap gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                assignment.status === "completed" ? "bg-green-100 text-green-700" :
                assignment.status === "overdue" ? "bg-red-100 text-red-700" :
                assignment.status === "in_progress" ? "bg-blue-100 text-blue-700" :
                "bg-yellow-100 text-yellow-700"
              }`}>
                {assignment.status.replace("_", " ")}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                assignment.priority === "urgent" ? "bg-red-100 text-red-700" :
                assignment.priority === "high" ? "bg-orange-100 text-orange-700" :
                assignment.priority === "medium" ? "bg-blue-100 text-blue-700" :
                "bg-gray-100 text-gray-700"
              }`}>
                {assignment.priority}
              </span>
              {assignment.tags?.map((tag) => (
                <span key={tag} className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {tag}
                </span>
              ))}
            </div>

            {assignment.description && (
              <div>
                <h3 className="mb-1 text-sm font-medium text-muted-foreground">Description</h3>
                <p className="text-sm whitespace-pre-wrap">{assignment.description}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              {assignment.subject_id && (
                <div><span className="text-muted-foreground">Subject:</span> {assignment.subject_id}</div>
              )}
              {assignment.due_date && (
                <div>
                  <span className="text-muted-foreground">Due:</span>{" "}
                  {new Date(assignment.due_date).toLocaleDateString()}
                </div>
              )}
              {assignment.estimated_study_time && (
                <div><span className="text-muted-foreground">Est. time:</span> {assignment.estimated_study_time} min</div>
              )}
              {assignment.completion_date && (
                <div>
                  <span className="text-muted-foreground">Completed:</span>{" "}
                  {new Date(assignment.completion_date).toLocaleDateString()}
                </div>
              )}
              <div><span className="text-muted-foreground">Created:</span> {new Date(assignment.created_at).toLocaleDateString()}</div>
            </div>

            {assignment.notes && (
              <div>
                <h3 className="mb-1 text-sm font-medium text-muted-foreground">Notes</h3>
                <p className="text-sm whitespace-pre-wrap text-muted-foreground">{assignment.notes}</p>
              </div>
            )}

            <div>
              <h3 className="mb-2 text-sm font-medium text-muted-foreground">Attachments</h3>
              <div className="space-y-2">
                {attachments?.map((att) => (
                  <div key={att.id} className="flex items-center justify-between rounded-lg border px-3 py-2">
                    <div className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                      <span className="text-sm">{att.file_name}</span>
                      {att.file_size && (
                        <span className="text-xs text-muted-foreground">
                          ({(att.file_size / 1024).toFixed(0)} KB)
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => deleteAttachmentMutation.mutate(att.id)}
                      className="text-xs text-destructive hover:text-destructive/80"
                    >
                      Delete
                    </button>
                  </div>
                ))}
                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed px-3 py-2 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  Upload file
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) uploadMutation.mutate(file);
                    }}
                  />
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="outline" onClick={() => onEdit(assignment)}>Edit</Button>
            </div>
          </div>
        ) : null}
      </motion.div>
    </div>
  );
}
