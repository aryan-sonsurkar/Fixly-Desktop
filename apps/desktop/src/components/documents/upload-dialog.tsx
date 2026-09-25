import { useState, useCallback, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button } from "@fixly/ui";
import { DocumentFilename } from "@/components/documents/document-filename";
import { motion, AnimatePresence } from "framer-motion";

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUpload: (files: File[]) => Promise<void>;
}

const ALLOWED_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
];

const ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp"];
const MAX_SIZE_BYTES = 50 * 1024 * 1024;

export type FileCheck = { ok: true } | { ok: false; reason: string };

function fileExtension(name: string): string {
  const parts = name.split(".");
  return (parts.length > 1 ? parts.pop() : "")?.toLowerCase() ?? "";
}

/** Pure, unit-testable pre-upload validation. Never inspects file contents. */
export function checkPickedFile(file: { name: string; type: string; size: unknown }): FileCheck {
  const size = typeof file.size === "number" ? file.size : Number.NaN;
  if (!isAllowedFile(file as File)) {
    return { ok: false, reason: "type" };
  }
  if (!Number.isFinite(size) || size <= 0) {
    return { ok: false, reason: "empty" };
  }
  if (size > MAX_SIZE_BYTES) {
    return { ok: false, reason: "size" };
  }
  return { ok: true };
}

export { MAX_SIZE_BYTES };

function isAllowedFile(file: File): boolean {
  // Tauri file metadata can carry a blank MIME type: fall back to extension.
  if (ALLOWED_TYPES.includes(file.type)) return true;
  return ALLOWED_EXTENSIONS.includes(fileExtension(file.name));
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function getTypeLabel(file: File): string {
  if (file.type === "application/pdf") return "PDF";
  if (file.type.startsWith("image/")) return file.type.split("/")[1].toUpperCase();
  return fileExtension(file.name).toUpperCase() || "FILE";
}

export function UploadDialog({ open, onClose, onUpload }: UploadDialogProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [rejected, setRejected] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((incoming: File[]) => {
    const ok: File[] = [];
    for (const f of incoming) {
      const check = checkPickedFile(f);
      if (!check.ok) {
        if (check.reason === "size") {
          setRejected(`"${f.name}" is larger than 50 MB.`);
        } else if (check.reason === "empty") {
          setRejected(`"${f.name}" is empty.`);
        } else {
          setRejected(`"${f.name}" isn't a supported file. PDF, PNG, JPG or WEBP up to 50 MB.`);
        }
        continue;
      }
      ok.push(f);
    }
    if (ok.length > 0) {
      setRejected(null);
      setFiles((prev) => [...prev, ...ok]);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    addFiles(Array.from(e.dataTransfer.files));
  }, [addFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files ? Array.from(e.target.files) : [];
    addFiles(selected);
  }, [addFiles]);

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      await onUpload(files);
      setFiles([]);
      onClose();
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setFiles([]);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div
            onDragOver={(e) => (e.preventDefault(), setDragOver(true))}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
          >
            <svg className="h-10 w-10 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <div>
              <p className="text-sm font-medium">Drop files here or click to browse</p>
              <p className="mt-1 text-xs text-muted-foreground">PDF, PNG, JPG, WEBP up to 50 MB</p>
            </div>
            <input ref={inputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp" className="hidden" onChange={handleFileSelect} />
          </div>

          <AnimatePresence>
            {rejected && (
              <p className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
                {rejected}
              </p>
            )}
            {files.map((file, i) => (
              <motion.div
                key={`${file.name}-${i}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="flex items-center gap-3 rounded-lg border bg-card p-3"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded bg-muted text-xs font-bold text-muted-foreground uppercase">
                  {getTypeLabel(file)}
                </div>
                <div className="flex-1 min-w-0">
                  <DocumentFilename name={file.name} />
                  <p className="text-xs text-muted-foreground">{formatSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  disabled={uploading}
                  className="rounded p-1 text-muted-foreground hover:text-destructive disabled:opacity-50"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </motion.div>
            ))}
          </AnimatePresence>

          {files.length > 0 && (
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={handleClose} disabled={uploading}>
                Cancel
              </Button>
              <Button onClick={handleUpload} disabled={uploading}>
                {uploading ? "Uploading..." : `Upload ${files.length} file${files.length !== 1 ? "s" : ""}`}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
