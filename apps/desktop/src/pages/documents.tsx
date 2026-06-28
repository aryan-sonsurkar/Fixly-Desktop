import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Button, Input, Badge, Skeleton } from "@fixly/ui";
import { UploadDialog } from "@/components/documents/upload-dialog";
import { DocumentChat } from "@/components/documents/document-chat";
import {
  listDocuments,
  getDocument,
  uploadDocument,
  processDocument,
  deleteDocument,
  updateDocument,
  summarizeDocument,
  generateNotes,
  generateFlashcards,
  generateQuiz,
  type Document,
  type DocumentDetail,
} from "@/lib/document-service";

const typeColors: Record<string, string> = {
  pdf: "bg-red-500/10 text-red-500",
  png: "bg-blue-500/10 text-blue-500",
  jpg: "bg-green-500/10 text-green-500",
  jpeg: "bg-green-500/10 text-green-500",
  webp: "bg-purple-500/10 text-purple-500",
};

const statusColors: Record<string, string> = {
  pending: "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400",
  processing: "text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400",
  processed: "text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400",
  failed: "text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function DocumentCard({ doc, onSelect, onDelete, onFavorite }: {
  doc: Document;
  onSelect: () => void;
  onDelete: () => void;
  onFavorite: () => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="group cursor-pointer rounded-lg border bg-card p-4 transition-shadow hover:shadow-md"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded text-xs font-bold ${typeColors[doc.file_type] || "bg-muted text-muted-foreground"}`}>
            {doc.file_type.toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{doc.original_name}</p>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{formatSize(doc.file_size)}</span>
              {doc.page_count > 0 && <span>&middot; {doc.page_count}p</span>}
              <span>&middot; {formatDate(doc.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => (e.stopPropagation(), onFavorite())}
            className={`rounded p-1 transition-colors ${
              doc.is_favorite ? "text-yellow-500" : "text-muted-foreground opacity-0 group-hover:opacity-100"
            }`}
          >
            <svg className="h-4 w-4" fill={doc.is_favorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
          <button
            type="button"
            onClick={(e) => (e.stopPropagation(), onDelete())}
            className="rounded p-1 text-muted-foreground opacity-0 transition-colors hover:text-destructive group-hover:opacity-100"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <Badge variant="outline" className={statusColors[doc.status] || ""}>
          {doc.status === "processing" ? "Processing..." : doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
        </Badge>
      </div>
    </motion.div>
  );
}

function DocumentViewer({ doc, onBack }: { doc: DocumentDetail; onBack: () => void }) {
  const [activeTab, setActiveTab] = useState<"chat" | "actions">("chat");

  const handleAction = async (action: () => Promise<unknown>) => {
    try {
      await action();
    } catch (err) {
      console.error("Action failed:", err);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b px-4 py-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </Button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{doc.original_name}</p>
          <p className="text-xs text-muted-foreground">
            {doc.file_type.toUpperCase()} &middot; {formatSize(doc.file_size)}
            {doc.page_count > 0 && ` &middot; ${doc.page_count} pages`}
          </p>
        </div>
        <div className="flex gap-1">
          <Button
            variant={activeTab === "chat" ? "default" : "ghost"} size="sm"
            onClick={() => setActiveTab("chat")}
          >
            Chat
          </Button>
          <Button
            variant={activeTab === "actions" ? "default" : "ghost"} size="sm"
            onClick={() => setActiveTab("actions")}
          >
            Actions
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === "chat" ? (
          <DocumentChat documentId={doc.id} />
        ) : (
          <div className="grid grid-cols-2 gap-2 p-4">
            <ActionButton
              label="Summarize"
              icon="M4 6h16M4 12h16M4 18h7"
              onClick={() => handleAction(() => summarizeDocument(doc.id))}
            />
            <ActionButton
              label="Generate Notes"
              icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              onClick={() => handleAction(() => generateNotes(doc.id))}
            />
            <ActionButton
              label="Flashcards"
              icon="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              onClick={() => handleAction(() => generateFlashcards(doc.id))}
            />
            <ActionButton
              label="Quiz"
              icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              onClick={() => handleAction(() => generateQuiz(doc.id))}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({ label, icon, onClick }: { label: string; icon: string; onClick: () => void }) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="flex flex-col items-center gap-2 rounded-lg border bg-card p-4 text-sm transition-colors hover:bg-accent"
    >
      <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
      </svg>
      <span>{label}</span>
    </motion.button>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents", search, filterType],
    queryFn: () => listDocuments({ search: search || undefined, file_type: filterType || undefined, page_size: 50 }),
  });

  const { data: selectedDoc } = useQuery({
    queryKey: ["document", selectedDocId],
    queryFn: () => selectedDocId ? getDocument(selectedDocId) : Promise.resolve(null),
    enabled: !!selectedDocId,
  });

  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      for (const file of files) {
        const doc = await uploadDocument(file);
        await processDocument(doc.id);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const handleDelete = async (id: string) => {
    await deleteDocument(id);
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    if (selectedDocId === id) setSelectedDocId(null);
  };

  const handleFavorite = async (doc: Document) => {
    await updateDocument(doc.id, { is_favorite: !doc.is_favorite });
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  if (selectedDoc) {
    return (
      <div className="mx-auto flex h-full max-w-7xl flex-col">
        <DocumentViewer doc={selectedDoc} onBack={() => setSelectedDocId(null)} />
      </div>
    );
  }

  const docs = data?.documents || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-sm text-muted-foreground">Upload and analyze PDFs, images, and more</p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>
          <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Upload
        </Button>
      </motion.div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <Input
            className="pl-9"
            placeholder="Search documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-1">
          {["all", "pdf", "png", "jpg", "webp"].map((type) => (
            <Button
              key={type}
              variant={filterType === type || (type === "all" && !filterType) ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterType(type === "all" ? null : type)}
            >
              {type.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      ) : docs.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <svg className="h-16 w-16 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <p className="text-sm text-muted-foreground">No documents yet</p>
          <Button onClick={() => setUploadOpen(true)}>Upload your first document</Button>
        </div>
      ) : (
        <AnimatePresence>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {docs.map((doc) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onSelect={() => setSelectedDocId(doc.id)}
                onDelete={() => handleDelete(doc.id)}
                onFavorite={() => handleFavorite(doc)}
              />
            ))}
          </div>
        </AnimatePresence>
      )}

      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUpload={(files) => uploadMutation.mutateAsync(files)}
      />
    </div>
  );
}
