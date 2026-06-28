import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import type { Assignment } from "@fixly/shared-types";

interface AssignmentCardProps {
  assignment: Assignment;
  subjectName?: string;
  subjectColor?: string | null;
  isSelected: boolean;
  onToggleSelect: () => void;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const priorityColors: Record<string, string> = {
  urgent: "text-red-500 bg-red-500/10",
  high: "text-orange-500 bg-orange-500/10",
  medium: "text-blue-500 bg-blue-500/10",
  low: "text-gray-500 bg-gray-500/10",
};

const statusColors: Record<string, string> = {
  pending: "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400",
  in_progress: "text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400",
  completed: "text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400",
  overdue: "text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400",
  cancelled: "text-gray-500 bg-gray-100 dark:bg-gray-800 dark:text-gray-400",
};

export function AssignmentCard({
  assignment,
  subjectName,
  subjectColor,
  isSelected,
  onToggleSelect,
  onClick,
  onEdit,
  onDelete,
  onDuplicate,
}: AssignmentCardProps) {
  const isOverdue = assignment.status === "overdue";
  const isDueSoon =
    assignment.due_date &&
    !isOverdue &&
    assignment.status !== "completed" &&
    new Date(assignment.due_date).getTime() - Date.now() < 86400000 * 2;

  return (
    <motion.div
      layout
      className={`group relative rounded-lg border bg-card p-4 transition-all hover:shadow-md ${
        isSelected ? "border-primary ring-1 ring-primary" : ""
      } ${isOverdue ? "border-l-4 border-l-red-500" : isDueSoon ? "border-l-4 border-l-orange-400" : ""}`}
    >
      <div className="flex items-center gap-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="h-4 w-4 accent-primary"
        />

        <div className="flex-1 min-w-0 cursor-pointer" onClick={onClick}>
          <div className="flex items-center gap-2">
            {assignment.is_pinned && (
              <svg className="h-3.5 w-3.5 text-primary" fill="currentColor" viewBox="0 0 24 24">
                <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
              </svg>
            )}
            {assignment.is_favorite && (
              <svg className="h-3.5 w-3.5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            )}
            <p className="truncate text-sm font-medium">{assignment.title}</p>
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            {subjectName && (
              <span className="flex items-center gap-1">
                {subjectColor && <span className="h-2 w-2 rounded-full" style={{ backgroundColor: subjectColor }} />}
                {subjectName}
              </span>
            )}
            {assignment.due_date && (
              <span>
                Due: {new Date(assignment.due_date).toLocaleDateString()}
              </span>
            )}
            {assignment.tags && assignment.tags.length > 0 && (
              <span className="hidden md:inline">{assignment.tags.slice(0, 2).join(", ")}</span>
            )}
          </div>
        </div>

        <span className={`hidden rounded-full px-2 py-0.5 text-xs font-medium md:inline ${priorityColors[assignment.priority] || priorityColors.medium}`}>
          {assignment.priority}
        </span>

        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[assignment.status] || statusColors.pending}`}>
          {assignment.status.replace("_", " ")}
        </span>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="sm" onClick={onEdit}>Edit</Button>
          <Button variant="ghost" size="sm" onClick={onDuplicate}>Copy</Button>
          <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={onDelete}>
            Delete
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
