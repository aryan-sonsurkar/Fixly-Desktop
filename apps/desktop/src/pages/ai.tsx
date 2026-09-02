import { useEffect, useState } from "react";
import { ConversationSidebar } from "@/components/ai/conversation-sidebar";
import { ChatWindow } from "@/components/ai/chat-window";
import { AISettingsDialog } from "@/components/ai/ai-settings-dialog";
import { useAIStore } from "@/stores/ai-store";
import * as aiService from "@/lib/ai-service";

export default function AIPage() {
  const {
    setSettings, setSettingsOpen, error, setError,
  } = useAIStore();

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const s = await aiService.getAISettings();
        setSettings(s);
      } catch {
        setError("Failed to load AI settings");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [setSettings, setError]);

  return (
    <div className="flex h-[calc(100dvh-56px)] min-h-0 flex-col bg-background">
      <header className="flex shrink-0 items-center justify-between border-b bg-card/80 backdrop-blur px-4 py-2.5">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold tracking-tight">Fixly AI</h1>
          {loading && <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent"
            title="AI Settings"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </header>

      {error && (
        <div className="flex items-center gap-2 border-b bg-destructive/10 px-4 py-2 text-sm text-destructive">
          <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <span className="flex-1">{error}</span>
          <button type="button" onClick={() => setError(null)} className="rounded p-0.5 hover:bg-destructive/20">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden bg-muted/20">
        <div className="w-72 shrink-0 border-r bg-card">
          <ConversationSidebar />
        </div>

        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>
      </div>

      <AISettingsDialog />
    </div>
  );
}
