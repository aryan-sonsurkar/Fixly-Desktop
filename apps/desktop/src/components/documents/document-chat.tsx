import { useState, useRef, useEffect } from "react";
import { Button } from "@fixly/ui";
import { motion, AnimatePresence } from "framer-motion";
import { chatWithDocument } from "@/lib/document-service";
import { MarkdownRenderer } from "@/components/ai/markdown-renderer";
import { SourceCitations, type Citation } from "@/components/ai/source-citations";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations?: Citation[];
}

interface DocumentChatProps {
  documentId: string;
  docTitle?: string;
  conversationId?: string;
  onConversationCreated?: (id: string) => void;
}

const SUGGESTIONS = [
  "Summarize this chapter",
  "What are the key concepts?",
  "Explain this in simple language",
  "Make me a quiz",
];

export function DocumentChat({ documentId, docTitle, conversationId, onConversationCreated }: DocumentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState(conversationId);
  const [failedPrompt, setFailedPrompt] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    setLoading(true);
    setFailedPrompt(null);

    try {
      const result = await chatWithDocument({
        document_id: documentId,
        message: trimmed,
        conversation_id: convId,
      });

      if (!convId && result.conversation?.id) {
        setConvId(result.conversation.id);
        onConversationCreated?.(result.conversation.id);
      }

      const citations: Citation[] | undefined = Array.isArray(result.chunks_used)
        ? result.chunks_used
            .map((c: { heading?: string | null; page_number?: number | null }) => ({
              type: "document" as const,
              title: docTitle || "Document",
              page: typeof c.page_number === "number" ? c.page_number : undefined,
            }))
            .filter((c: Citation) => c.page !== undefined)
            .slice(0, 5)
        : undefined;

      const assistantMsg: Message = {
        id: result.message.id,
        role: "assistant",
        content: result.message.content,
        created_at: result.message.created_at,
        citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setFailedPrompt(trimmed);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    void send(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const autoGrow = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  return (
    <div className="mx-auto flex h-full w-full max-w-[850px] flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center gap-5 py-10 text-center">
            <div>
              <p className="text-base font-semibold">Ask anything about this document.</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Answers come straight from the text, with page references.
              </p>
            </div>
            <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => void send(s)}
                  className="rounded-xl border bg-card px-4 py-3 text-left text-sm transition-colors hover:border-primary/30 hover:bg-accent/50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg) =>
            msg.role === "user" ? (
              <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
                <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  {msg.content}
                </div>
              </motion.div>
            ) : (
              <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-start">
                <div className="w-full max-w-3xl">
                  <MarkdownRenderer content={msg.content} />
                  {msg.citations && msg.citations.length > 0 && (
                    <SourceCitations citations={msg.citations} />
                  )}
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </motion.div>
            ),
          )}
        </AnimatePresence>

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-3 text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
              Fixly AI is generating…
            </div>
          </div>
        )}

        {failedPrompt && !loading && (
          <div className="flex justify-start">
            <div className="flex max-w-[80%] flex-col gap-2 rounded-2xl border border-destructive/20 bg-destructive/5 px-4 py-3">
              <p className="text-sm">Fixly couldn&apos;t complete that response.</p>
              <button
                type="button"
                onClick={() => void send(failedPrompt)}
                className="self-start rounded-lg bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t bg-card px-4 py-3">
        <div className="relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              autoGrow();
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this document..."
            rows={2}
            className="max-h-[160px] w-full resize-none rounded-xl border bg-background px-4 py-3 pr-14 text-sm outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          />
          <Button
            size="sm"
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="absolute bottom-2.5 right-2.5 h-9 px-4"
          >
            Send
          </Button>
        </div>
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
          Answers use this document and show page sources.
        </p>
      </div>
    </div>
  );
}
