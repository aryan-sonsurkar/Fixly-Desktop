import { motion } from "framer-motion";
import { Button } from "@fixly/ui";

interface AssignmentEmptyStateProps {
  hasFilters: boolean;
  onCreateNew: () => void;
}

export function AssignmentEmptyState({ hasFilters, onCreateNew }: AssignmentEmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <svg className="h-8 w-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="mb-1 text-lg font-medium">
        {hasFilters ? "No matching assignments" : "No assignments yet"}
      </h3>
      <p className="mb-6 text-sm text-muted-foreground">
        {hasFilters
          ? "Try adjusting your filters or search query."
          : "Create your first assignment to get started."}
      </p>
      {!hasFilters && (
        <Button onClick={onCreateNew}>Create Assignment</Button>
      )}
    </motion.div>
  );
}
