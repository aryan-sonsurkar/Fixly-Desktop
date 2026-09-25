import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDebouncedValue } from "@/hooks/use-debounce";
import { motion, AnimatePresence } from "framer-motion";
import { Button, Input, Badge, Skeleton } from "@fixly/ui";
import { UploadDialog } from "@/components/documents/upload-dialog";
import { DocumentChat } from "@/components/documents/document-chat";
import { DocumentFilename } from "@/components/documents/document-filename";
import { MarkdownRenderer } from "@/components/ai/markdown-renderer";
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
  type DocumentCard as FlashcardData,
  type QuizQuestion,
  type DocumentSource,
  type GenerateContentResponse,
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
  indexed: "text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400",
  empty: "text-amber-600 bg-amber-100 dark:bg-amber-900/20 dark:text-amber-400",
  failed: "text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400",
};

const statusLabels: Record<string, string> = {
  pending: "Pending",
  processing: "Processing...",
  processed: "Ready",
  indexed: "Ready",
  empty: "No readable text",
  failed: "Couldn't process",
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

function DocumentCard({ doc, onSelect, onDelete, onFavorite, onRetry }: {
  doc: Document;
  onSelect: () => void;
  onDelete: () => void;
  onFavorite: () => void;
  onRetry: () => void;
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
          <div className="min-w-0 flex-1">
            <DocumentFilename name={doc.original_name} />
            <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{formatSize(doc.file_size)}</span>
              {doc.page_count > 0 && <span>&middot; {doc.page_count} pages</span>}
              <span>&middot; {formatDate(doc.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => (e.stopPropagation(), onFavorite())}
            className={`rounded p-1 transition-colors focus:opacity-100 focus-visible:opacity-100 group-focus-within:opacity-100 ${
              doc.is_favorite ? "text-yellow-500" : "text-muted-foreground opacity-0 group-hover:opacity-100"
            }`}
            aria-label={doc.is_favorite ? "Unfavorite" : "Favorite"}
          >
            <svg className="h-4 w-4" fill={doc.is_favorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
          <button
            type="button"
            onClick={(e) => (e.stopPropagation(), onDelete())}
            className="rounded p-1 text-muted-foreground opacity-0 transition-colors hover:text-destructive group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100 focus-visible:opacity-100"
            aria-label="Delete document"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <Badge variant="outline" className={statusColors[doc.status] || ""}>
          {statusLabels[doc.status] || doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
        </Badge>
        {doc.status === "empty" && (
          <span className="text-[11px] text-muted-foreground">Scanned/image PDF? Text chat still works.</span>
        )}
        {doc.status === "failed" && (
          <button
            type="button"
            onClick={(e) => (e.stopPropagation(), onRetry())}
            className="rounded-md border px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            Retry
          </button>
        )}
      </div>
    </motion.div>
  );
}

function DocumentViewer({ doc, onBack }: { doc: DocumentDetail; onBack: () => void }) {
  const [activeTab, setActiveTab] = useState<"chat" | "actions">("chat");

  type ActionKind = "summarize" | "notes" | "flashcards" | "quiz";
  interface ActionState {
    status: "idle" | "generating" | "success" | "error";
    result: GenerateContentResponse | null;
  }
  const [actions, setActions] = useState<Record<ActionKind, ActionState>>({
    summarize: { status: "idle", result: null },
    notes: { status: "idle", result: null },
    flashcards: { status: "idle", result: null },
    quiz: { status: "idle", result: null },
  });

  const runAction = async (kind: ActionKind, fn: () => Promise<GenerateContentResponse>) => {
    setActions((prev) => ({ ...prev, [kind]: { status: "generating", result: prev[kind].result } }));
    try {
      const result = await fn();
      setActions((prev) => ({ ...prev, [kind]: { status: "success", result } }));
    } catch {
      setActions((prev) => ({ ...prev, [kind]: { status: "error", result: prev[kind].result } }));
    }
  };

  const retryAction = (kind: ActionKind) => {
    if (kind === "summarize") runAction(kind, () => summarizeDocument(doc.id));
    else if (kind === "notes") runAction(kind, () => generateNotes(doc.id));
    else if (kind === "flashcards") runAction(kind, () => generateFlashcards(doc.id));
    else runAction(kind, () => generateQuiz(doc.id));
  };

  const generatingLabels: Record<ActionKind, string> = {
    summarize: "Reading document…",
    notes: "Generating summary…",
    flashcards: "Building flashcards from your notes…",
    quiz: "Building quiz from your notes…",
  };

  const docReady = doc.status === "indexed" || doc.status === "processed";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b px-4 py-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </Button>
        <div className="min-w-0 flex-1">
          <DocumentFilename name={doc.original_name} />
          <p className="mt-0.5 text-xs text-muted-foreground">
            {doc.file_type.toUpperCase()} &middot; {formatSize(doc.file_size)}
            {doc.page_count > 0 && ` &middot; ${doc.page_count} pages`}
            &middot; {doc.status === "indexed" || doc.status === "processed" ? "Ready" : doc.status}
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

      <div className="flex-1 overflow-y-auto">
        {activeTab === "chat" ? (
          <DocumentChat documentId={doc.id} docTitle={doc.original_name} />
        ) : (
          <div className="mx-auto w-full max-w-3xl space-y-3 p-4">
            {!docReady && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-600">
                {doc.status === "empty"
                  ? "This document has no extractable text, so actions are unavailable."
                  : "Document is still being processed. Actions will work when it's ready."}
              </div>
            )}
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <ActionButton
                label="Summarize"
                desc="Get the key ideas"
                icon="M4 6h16M4 12h16M4 18h7"
                disabled={!docReady}
                loading={actions.summarize.status === "generating"}
                onClick={() => runAction("summarize", () => summarizeDocument(doc.id))}
              />
              <ActionButton
                label="Study Notes"
                desc="Turn this into structured notes"
                icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                disabled={!docReady}
                loading={actions.notes.status === "generating"}
                onClick={() => runAction("notes", () => generateNotes(doc.id))}
              />
              <ActionButton
                label="Flashcards"
                desc="Practice active recall"
                icon="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                disabled={!docReady}
                loading={actions.flashcards.status === "generating"}
                onClick={() => runAction("flashcards", () => generateFlashcards(doc.id))}
              />
              <ActionButton
                label="Quiz"
                desc="Test what you know"
                icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                disabled={!docReady}
                loading={actions.quiz.status === "generating"}
                onClick={() => runAction("quiz", () => generateQuiz(doc.id))}
              />
            </div>
            {(["summarize", "notes", "flashcards", "quiz"] as ActionKind[]).map((kind) =>
              actions[kind].status === "generating" ? (
                <div key={`${kind}-loading`} className="flex items-center gap-2 rounded-lg border bg-card px-4 py-3 text-sm text-muted-foreground">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                  {generatingLabels[kind]}
                </div>
              ) : actions[kind].status === "error" ? (
                <div key={`${kind}-error`} className="flex items-center justify-between gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm">
                  <span className="text-destructive">Couldn&apos;t complete that action. Please try again.</span>
                  <Button size="sm" variant="outline" onClick={() => retryAction(kind)}>
                    Retry
                  </Button>
                </div>
              ) : actions[kind].status === "success" && actions[kind].result ? (
                <ActionResult
                  key={`${kind}-result`}
                  kind={kind}
                  result={actions[kind].result as GenerateContentResponse}
                />
              ) : null,
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({ label, desc, icon, onClick, disabled, loading }: {
  label: string;
  desc: string;
  icon: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
}) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.01 }}
      whileTap={disabled ? undefined : { scale: 0.99 }}
      onClick={onClick}
      disabled={disabled || loading}
      className="flex items-center gap-3 rounded-xl border bg-card p-4 text-left transition-colors hover:border-primary/30 hover:bg-accent/50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
        {loading ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        ) : (
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
          </svg>
        )}
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-medium">{label}</span>
        <span className="block truncate text-xs text-muted-foreground">{loading ? "Working…" : desc}</span>
      </span>
    </motion.button>
  );
}

function SourcesLine({ sources }: { sources: DocumentSource[] }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 border-t pt-2">
      <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Sources</p>
      {sources.map((s, i) => (
        <p key={i} className="mt-0.5 truncate text-xs text-muted-foreground">
          {s.title}
          {s.pages.length > 0 && (
            <span> &middot; p.{s.pages.slice(0, 6).join(", p.")}{s.pages.length > 6 ? ` +${s.pages.length - 6} more` : ""}</span>
          )}
        </p>
      ))}
    </div>
  );
}

function ActionResult({ kind, result }: {
  kind: "summarize" | "notes" | "flashcards" | "quiz";
  result: GenerateContentResponse;
}) {
  if (kind === "flashcards") {
    return (
      <div className="rounded-xl border bg-card p-4">
        <p className="mb-3 text-sm font-semibold">Flashcards</p>
        {result.cards.length > 0 ? (
          <FlashcardDeck cards={result.cards} />
        ) : (
          <MarkdownRenderer content={result.content} />
        )}
        <SourcesLine sources={result.sources} />
      </div>
    );
  }
  if (kind === "quiz") {
    return (
      <div className="rounded-xl border bg-card p-4">
        <p className="mb-3 text-sm font-semibold">Quiz</p>
        {result.questions.length > 0 ? (
          <QuizRunner questions={result.questions} />
        ) : (
          <MarkdownRenderer content={result.content} />
        )}
        <SourcesLine sources={result.sources} />
      </div>
    );
  }
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="mb-2 text-sm font-semibold">{kind === "summarize" ? "Summary" : "Study Notes"}</p>
      <MarkdownRenderer content={result.content} />
      <SourcesLine sources={result.sources} />
    </div>
  );
}

function FlashcardDeck({ cards }: { cards: FlashcardData[] }) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const card = cards[Math.min(index, cards.length - 1)];
  if (!card) return null;
  return (
    <div>
      <button
        type="button"
        onClick={() => setFlipped((f) => !f)}
        className="flex min-h-32 w-full flex-col items-center justify-center gap-2 rounded-lg bg-muted/50 px-4 py-6 text-center transition-colors hover:bg-muted"
        aria-label={flipped ? "Show front" : "Show back"}
      >
        <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          {flipped ? "Answer" : "Question"} &middot; {index + 1}/{cards.length}
        </span>
        <span className="text-sm">{flipped ? card.back || "(no answer)" : card.front}</span>
        <span className="text-[11px] text-muted-foreground">Tap to flip</span>
      </button>
      <div className="mt-2 flex items-center justify-between">
        <Button
          size="sm" variant="outline"
          disabled={index === 0}
          onClick={() => { setIndex((i) => Math.max(0, i - 1)); setFlipped(false); }}
        >
          Previous
        </Button>
        <Button
          size="sm" variant="outline"
          disabled={index >= cards.length - 1}
          onClick={() => { setIndex((i) => Math.min(cards.length - 1, i + 1)); setFlipped(false); }}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

function QuizRunner({ questions }: { questions: QuizQuestion[] }) {
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);
  const q = questions[Math.min(index, questions.length - 1)];
  if (!q) return null;

  const checkAnswer = (choice: string) => {
    if (picked !== null) return;
    setPicked(choice);
    if (choice.trim().toLowerCase() === q.answer.trim().toLowerCase()) {
      setScore((s) => s + 1);
    }
  };

  const next = () => {
    if (index >= questions.length - 1) {
      setDone(true);
      return;
    }
    setIndex((i) => i + 1);
    setPicked(null);
  };

  if (done) {
    return (
      <div className="rounded-lg bg-muted/50 px-4 py-6 text-center">
        <p className="text-sm font-semibold">Score: {score}/{questions.length}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {score === questions.length ? "Perfect — nice work." : "Review the material and try again."}
        </p>
        <Button
          size="sm" variant="outline" className="mt-3"
          onClick={() => { setIndex(0); setPicked(null); setScore(0); setDone(false); }}
        >
          Retry quiz
        </Button>
      </div>
    );
  }

  const isCorrect = picked !== null && picked.trim().toLowerCase() === q.answer.trim().toLowerCase();
  return (
    <div>
      <p className="text-[11px] text-muted-foreground">Question {index + 1}/{questions.length}</p>
      <p className="mt-1 text-sm font-medium">{q.question}</p>
      <div className="mt-2 space-y-1.5">
        {(q.options.length > 0 ? q.options : ["True", "False"]).map((opt) => {
          const selected = picked === opt;
          const isAnswer = opt.trim().toLowerCase() === q.answer.trim().toLowerCase();
          return (
            <button
              key={opt}
              type="button"
              disabled={picked !== null && q.options.length === 0}
              onClick={() => (q.options.length > 0 ? checkAnswer(opt) : setPicked(opt))}
              className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                picked === null
                  ? "hover:bg-accent"
                  : selected && isCorrect
                    ? "border-green-500/50 bg-green-500/10"
                    : selected
                      ? "border-destructive/50 bg-destructive/10"
                      : isAnswer && q.options.length > 0
                        ? "border-green-500/50 bg-green-500/10"
                        : "opacity-70"
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
      {picked !== null && (
        <div className="mt-2 rounded-lg bg-muted/50 px-3 py-2 text-xs">
          <p className={isCorrect ? "font-medium text-green-600" : "font-medium text-destructive"}>
            {isCorrect ? "Correct." : `Not quite. Answer: ${q.answer}`}
          </p>
          {q.explanation && <p className="mt-1 text-muted-foreground">{q.explanation}</p>}
          <Button size="sm" variant="outline" className="mt-2" onClick={next}>
            {index >= questions.length - 1 ? "See score" : "Next"}
          </Button>
        </div>
      )}
    </div>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string | null>(null);
  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, isLoading, error: listError, isFetching } = useQuery({
    queryKey: ["documents", debouncedSearch, filterType],
    queryFn: () => listDocuments({ search: debouncedSearch || undefined, file_type: filterType || undefined, page_size: 50 }),
    staleTime: 30 * 1000,
    placeholderData: (prev) => prev,
  });

  const { data: selectedDoc } = useQuery({
    queryKey: ["document", selectedDocId],
    queryFn: () => selectedDocId ? getDocument(selectedDocId) : Promise.resolve(null),
    enabled: !!selectedDocId,
    staleTime: 60 * 1000,
  });

  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      // Drop exact duplicates already queued in this batch.
      const seen = new Set<string>();
      const unique = files.filter((f) => {
        const key = `${f.name}::${f.size}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      setUploadProgress(`Uploading 0/${unique.length}...`);
      setUploadError(null);
      // Safe metadata only (never contents): diagnoses picker/size issues.
      for (const f of unique) {
        const sizeBytes = typeof f.size === "number" ? f.size : NaN;
        console.debug(
          `[documents] picked file=${JSON.stringify(f.name)} ` +
            `sizeBytes=${sizeBytes} sizeMB=${Number.isFinite(sizeBytes) ? (sizeBytes / 1048576).toFixed(2) : "?"} ` +
            `type=${JSON.stringify(f.type || "")}`,
        );
      }
      const results = await Promise.allSettled(
        unique.map(async (file, idx) => {
          setUploadProgress(`Uploading ${idx + 1}/${unique.length}: ${file.name}`);
          const doc = await uploadDocument(file);
          setUploadProgress(`Processing ${idx + 1}/${unique.length}: ${file.name}`);
          try {
            await processDocument(doc.id);
          } catch (procErr) {
            // Post-processing error (e.g. OCR unavailable for image) should not mask that
            // the file was safely uploaded and stored in the database.
            console.warn(`[documents] Post-processing note for doc ${doc.id}:`, procErr);
          }
          return doc;
        }),
      );
      setUploadProgress(null);
      const failures = results.filter((r) => r.status === "rejected");
      if (failures.length > 0) {
        // Preserve the first underlying failure so onError can distinguish
        // auth/network/validation/server causes instead of a generic message.
        const first = failures[0];
        throw first.status === "rejected" && first.reason instanceof Error
          ? first.reason
          : new Error(`All ${unique.length} uploads failed`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: unknown) => {
      // Student-safe copy only; technical detail stays in logs.
      // Map the distinguishing failure so reports are diagnosable.
      // NOTE: check message text BEFORE bare status codes: a 422 carrying
      // "content mismatch" must not be misreported as a size error.
      console.error("[documents] Upload error:", err);
      const response =
        typeof err === "object" && err !== null && "response" in err
          ? (err as { response?: { data?: { error?: unknown; code?: unknown }; status?: unknown } }).response
          : undefined;
      const status = typeof response?.status === "number" ? response.status : undefined;
      const backendMessage = typeof response?.data?.error === "string" ? response.data.error : "";
      const backendCode = typeof response?.data?.code === "string" ? response.data.code : "";
      const text = `${backendCode} ${backendMessage} ${err instanceof Error ? err.message : ""}`.toLowerCase();
      let msg: string;
      if (status === 401) {
        msg = "Your session expired. Sign in again, then retry the upload.";
      } else if (status === 404) {
        msg = "Upload service not found. Restart Fixly and try again.";
      } else if (text.includes("50mb") || (text.includes("size") && text.includes("exceed"))) {
        msg = "One or more files exceed the 50 MB limit.";
      } else if (
        text.includes("unsupported") ||
        text.includes("extension") ||
        text.includes("does not match") ||
        text.includes("empty file")
      ) {
        msg = "That file couldn't be uploaded. Supported types: PDF, PNG, JPG, WEBP.";
      } else if (status === 422) {
        msg = "That file couldn't be uploaded. Check the file type and try again.";
      } else if (status !== undefined && status >= 500) {
        msg = "Fixly couldn't process the upload. Try again in a moment.";
      } else if (text.includes("timeout") || text.includes("timed out")) {
        msg = "The upload timed out. Check your connection and try a smaller file.";
      } else if (text.includes("network") || status === undefined) {
        msg = "Couldn't reach Fixly. Check that the app backend is running and try again.";
      } else {
        msg = "Couldn't upload these documents. Check the file type and try again.";
      }
      // Developer-readable detail (status + backend code only, no internals).
      const detail = status !== undefined || backendCode
        ? `(error ${status ?? "network"}${backendCode ? ` · ${backendCode}` : ""})`
        : null;
      setUploadError(detail ? `${msg} ${detail}` : msg);
      setUploadProgress(null);
    },
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => processDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => {
      setUploadError("Couldn't process this document. Try uploading it again.");
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

      {isLoading && !data ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : isFetching && data ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 opacity-60">
          {data.documents.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} onSelect={() => setSelectedDocId(doc.id)} onDelete={() => handleDelete(doc.id)} onFavorite={() => handleFavorite(doc)} onRetry={() => retryMutation.mutate(doc.id)} />
          ))}
        </div>
      ) : listError ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <svg className="h-16 w-16 text-destructive/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="text-sm text-destructive">Failed to load documents</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ["documents"] })}>Retry</Button>
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
                onRetry={() => retryMutation.mutate(doc.id)}
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

      {uploadProgress && (
        <div className="fixed bottom-4 left-1/2 z-40 -translate-x-1/2">
          <div className="flex items-center gap-2 rounded-full border bg-card px-4 py-2 text-xs shadow-lg">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
            {uploadProgress}
          </div>
        </div>
      )}
      {uploadError && (
        <div className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-xl border border-destructive/30 bg-card px-4 py-2.5 text-xs shadow-lg">
          <span className="text-destructive">{uploadError}</span>
          <button type="button" onClick={() => setUploadError(null)} className="text-muted-foreground underline hover:no-underline">
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
