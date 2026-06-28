import { motion, AnimatePresence } from "framer-motion";
import { Separator } from "@fixly/ui";
import { useAIStore } from "@/stores/ai-store";

export function ConversationInfoPanel() {
  const { infoPanelOpen, setInfoPanelOpen, currentConversationId, messages, conversations } = useAIStore();

  const conv = conversations.find((c) => c.id === currentConversationId);
  if (!currentConversationId || !conv) return null;

  const assistantMessages = messages.filter((m) => m.role === "assistant");
  const lastAssistant = assistantMessages[assistantMessages.length - 1];
  const totalTokens = assistantMessages.reduce((sum, m) => sum + (m.tokens || 0), 0);

  return (
    <AnimatePresence>
      {infoPanelOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 280, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          className="overflow-hidden border-l bg-card"
        >
          <div className="flex h-full w-[280px] flex-col">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <h3 className="text-sm font-semibold">Conversation Info</h3>
              <button
                type="button"
                onClick={() => setInfoPanelOpen(false)}
                className="rounded p-1 text-muted-foreground hover:bg-accent"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Provider</p>
                  <p className="mt-0.5 text-sm capitalize">{lastAssistant?.provider || "N/A"}</p>
                </div>

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground">Tokens Used</p>
                  <p className="mt-0.5 text-sm">{totalTokens.toLocaleString()}</p>
                </div>

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground">Messages</p>
                  <p className="mt-0.5 text-sm">{messages.length}</p>
                </div>

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground">Created</p>
                  <p className="mt-0.5 text-sm">{new Date(conv.created_at).toLocaleDateString()}</p>
                </div>

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground">Last Updated</p>
                  <p className="mt-0.5 text-sm">{new Date(conv.updated_at).toLocaleDateString()}</p>
                </div>

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground">Academic Context</p>
                  <p className="mt-0.5 text-sm text-green-600">Enabled</p>
                </div>

                <Separator />

                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Future AI Features</p>
                  <div className="space-y-1.5">
                    {[
                      { label: "PDF Analysis", icon: "📄", disabled: true },
                      { label: "Screenshot Analysis", icon: "📸", disabled: true },
                      { label: "OCR", icon: "🔤", disabled: true },
                      { label: "Email Intelligence", icon: "📧", disabled: true },
                    ].map((f) => (
                      <div
                        key={f.label}
                        className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 opacity-50"
                      >
                        <span className="text-xs">{f.icon}</span>
                        <span className="text-xs">{f.label}</span>
                        {f.disabled && <span className="ml-auto text-[10px] text-muted-foreground">Soon</span>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
