import { useState } from "react";
import { motion } from "framer-motion";
import { MarkdownRenderer } from "@/components/ai/markdown-renderer";
import type { Message } from "@/lib/ai-service";
import { setMessageFeedback, editMessage } from "@/lib/ai-service";
import { useAIStore } from "@/stores/ai-store";

interface MessageComponentProps {
  message: Message;
  onDelete?: (messageId: string) => void;
  onResend?: (content: string) => void;
}

export function MessageComponent({ message, onDelete, onResend }: MessageComponentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [feedback, setFeedback] = useState(message.feedback);
  const { updateMessage } = useAIStore();

  const isUser = message.role === "user";

  const handleFeedback = async (type: "like" | "dislike") => {
    const newFeedback = feedback === type ? null : type;
    try {
      await setMessageFeedback(message.id, newFeedback);
      setFeedback(newFeedback);
      updateMessage(message.id, { feedback: newFeedback });
    } catch {
      // silently fail
    }
  };

  const handleEditSave = async () => {
    if (!editContent.trim() || editContent === message.content) {
      setIsEditing(false);
      return;
    }
    try {
      await editMessage(message.id, editContent);
      updateMessage(message.id, { content: editContent });
      setIsEditing(false);
    } catch {
      // silently fail
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`group flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex max-w-[80%] flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "rounded-br-sm bg-primary text-primary-foreground"
              : "rounded-bl-sm bg-muted"
          }`}
        >
          {isEditing ? (
            <div className="flex flex-col gap-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[80px] w-full resize-none rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setIsEditing(false);
                    setEditContent(message.content);
                  }
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    handleEditSave();
                  }
                }}
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleEditSave}
                  className="rounded-md bg-primary px-3 py-1 text-xs text-primary-foreground hover:bg-primary/90"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setEditContent(message.content);
                  }}
                  className="rounded-md bg-secondary px-3 py-1 text-xs text-secondary-foreground hover:bg-secondary/80"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className={`${isUser ? "text-sm" : ""}`}>
              {isUser ? (
                message.content
              ) : (
                <MarkdownRenderer content={message.content} />
              )}
            </div>
          )}
        </div>

        <div className={`flex items-center gap-2 px-1 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
          <span className="text-[10px] text-muted-foreground">
            {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>

          {!isUser && message.provider && (
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
              {message.provider}
            </span>
          )}

          {!isUser && message.tokens != null && (
            <span className="text-[10px] text-muted-foreground">{message.tokens} tokens</span>
          )}

          <div className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
            {!isUser && (
              <>
                <button
                  type="button"
                  onClick={() => handleFeedback("like")}
                  className={`rounded p-0.5 transition-colors ${
                    feedback === "like" ? "text-green-500" : "text-muted-foreground hover:text-green-500"
                  }`}
                  title="Like"
                >
                  <svg className="h-3.5 w-3.5" fill={feedback === "like" ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 01-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 00-1.302 4.665c0 1.194.232 2.333.654 3.375z" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => handleFeedback("dislike")}
                  className={`rounded p-0.5 transition-colors ${
                    feedback === "dislike" ? "text-red-500" : "text-muted-foreground hover:text-red-500"
                  }`}
                  title="Dislike"
                >
                  <svg className="h-3.5 w-3.5" fill={feedback === "dislike" ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-.999 4.125m.023-8.25c-.076-.365.183-.75.575-.75h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398C20.613 14.547 19.833 15 19 15h-1.053c-.472 0-.745-.556-.5-.96a8.95 8.95 0 001.302-4.665c0-1.194-.232-2.333-.654-3.375z" />
                  </svg>
                </button>
              </>
            )}

            {isUser && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setEditContent(message.content);
                    setIsEditing(true);
                  }}
                  className="rounded p-0.5 text-muted-foreground hover:text-foreground"
                  title="Edit"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => onResend?.(message.content)}
                  className="rounded p-0.5 text-muted-foreground hover:text-foreground"
                  title="Resend"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                </button>
              </>
            )}

            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(message.id)}
                className="rounded p-0.5 text-muted-foreground hover:text-destructive"
                title="Delete"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
