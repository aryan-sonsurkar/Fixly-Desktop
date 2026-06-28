import { motion } from "framer-motion";
import { Button } from "@fixly/ui";

interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isDeleting: boolean;
  title?: string;
}

export function DeleteConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  isDeleting,
  title = "Delete this item?",
}: DeleteConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => onOpenChange(false)}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-sm rounded-2xl border bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">This action cannot be undone.</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isDeleting}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={isDeleting}>
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
