import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { useAIStore } from "@/stores/ai-store";
import * as aiService from "@/lib/ai-service";
import { MessageComponent } from "@/components/ai/message";
import { WelcomeScreen } from "@/components/ai/welcome-screen";

export function ChatWindow() {
  const {
    messages, currentConversationId, isStreaming, streamingContent, isSending,
    setIsStreaming, setStreamingContent, appendStreamingContent,
    addMessage, setIsSending, setError,
  } = useAIStore();

  const [input, setInput] = useState("");
  const [showStop, setShowStop] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowStop(false);
        setIsStreaming(false);
        abortRef.current?.abort();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setIsStreaming]);

  const handleSend = async (content?: string) => {
    const text = (content || input).trim();
    if (!text) return;

    setInput("");
    setIsSending(true);
    setError(null);

    try {
      let convId = currentConversationId;

      if (!convId) {
        const conv = await aiService.createConversation();
        convId = conv.id;
        useAIStore.getState().setCurrentConversationId(conv.id);
        useAIStore.getState().addConversation(conv);
        useAIStore.getState().setMessages([]);
      }

      const userMessage: aiService.Message = {
        id: `temp-${Date.now()}`,
        conversation_id: convId,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      addMessage(userMessage);

      setIsStreaming(true);
      setShowStop(true);
      setStreamingContent("");

      abortRef.current = new AbortController();

      const response = await aiService.sendChat({
        conversation_id: convId,
        message: text,
      });

      setShowStop(false);
      setIsStreaming(false);

      if (response.message) {
        addMessage(response.message);
      }

      if (response.conversation) {
        useAIStore.getState().updateConversation(convId, response.conversation);
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError("Failed to send message");
      setShowStop(false);
      setIsStreaming(false);
    } finally {
      setIsSending(false);
      abortRef.current = null;
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    try {
      await aiService.deleteMessage(messageId);
      useAIStore.getState().removeMessage(messageId);
    } catch {
      setError("Failed to delete message");
    }
  };

  const handleResend = async (content: string) => {
    await handleSend(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    setShowStop(false);
    setIsStreaming(false);
    abortRef.current?.abort();
  };

  if (!currentConversationId && messages.length === 0) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-1">
          <WelcomeScreen onSendPrompt={(prompt) => handleSend(prompt)} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.length === 0 && currentConversationId && (
            <div className="flex flex-col items-center justify-center py-12 text-center text-sm text-muted-foreground">
              <svg className="mb-3 h-10 w-10 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
              </svg>
              <p>Start a conversation by typing below</p>
            </div>
          )}

          {messages.map((message) => (
            <MessageComponent
              key={message.id}
              message={message}
              onDelete={message.role === "assistant" ? handleDeleteMessage : undefined}
              onResend={handleResend}
            />
          ))}

          {isStreaming && streamingContent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="max-w-[80%] rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
                <div className="whitespace-pre-wrap text-sm">{streamingContent}</div>
              </div>
            </motion.div>
          )}

          {isSending && !isStreaming && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "0ms" }} />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "150ms" }} />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t bg-card px-4 py-3">
        <div className="mx-auto max-w-3xl">
          {showStop && (
            <div className="mb-2 flex justify-center">
              <button
                type="button"
                onClick={handleStop}
                className="flex items-center gap-1.5 rounded-full bg-muted px-4 py-1.5 text-xs text-muted-foreground hover:bg-accent"
              >
                <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
                Stop generating
              </button>
            </div>
          )}

          <div className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message... (Ctrl+Enter to send)"
              rows={1}
              className="w-full resize-none rounded-xl border bg-background px-4 py-3 pr-12 text-sm outline-none focus:ring-2 focus:ring-primary"
              disabled={isSending}
            />
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={!input.trim() || isSending}
              className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </div>

          <p className="mt-1 text-center text-[10px] text-muted-foreground">
            Fixly AI may produce inaccurate information. Verify important details.
          </p>
        </div>
      </div>
    </div>
  );
}
