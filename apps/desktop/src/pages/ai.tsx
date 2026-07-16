import { useEffect, useState, useCallback } from "react";
import { ConversationSidebar } from "@/components/ai/conversation-sidebar";
import { ChatWindow } from "@/components/ai/chat-window";
import { ConversationInfoPanel } from "@/components/ai/conversation-info-panel";
import { AISettingsDialog } from "@/components/ai/ai-settings-dialog";
import { useAIStore } from "@/stores/ai-store";
import { useDashboardStore } from "@/stores/dashboard-store";
import * as aiService from "@/lib/ai-service";
import { interpretCommand } from "@/lib/copilot-service";

export default function AIPage() {
  const {
    setSettings, setSettingsOpen, setInfoPanelOpen, infoPanelOpen, error, setError,
  } = useAIStore();

  const { data: dashboardData } = useDashboardStore();
  const [loading, setLoading] = useState(true);
  const [showContext, setShowContext] = useState(false);
  const [copilotMode, setCopilotMode] = useState(false);
  const [smartInput, setSmartInput] = useState("");
  const [smartLoading, setSmartLoading] = useState(false);
  const [smartResult, setSmartResult] = useState<string | null>(null);

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

  const handleSmartCommand = useCallback(async () => {
    if (!smartInput.trim()) return;
    setSmartLoading(true);
    setSmartResult(null);
    try {
      const result = await interpretCommand(smartInput);
      setSmartResult(result.content);
    } catch {
      setSmartResult("Sorry, I couldn't process that command. Please try again.");
    } finally {
      setSmartLoading(false);
    }
  }, [smartInput]);

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b bg-card px-4 py-2">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold">AI Workspace</h1>
          {loading && <span className="text-xs text-muted-foreground">Loading...</span>}
          <button
            type="button"
            onClick={() => setShowContext(!showContext)}
            className={`rounded-lg px-2.5 py-1 text-xs transition-colors ${
              showContext ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent"
            }`}
          >
            Context
          </button>
          <button
            type="button"
            onClick={() => setCopilotMode(!copilotMode)}
            className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
              copilotMode
                ? "bg-violet-500/10 text-violet-500 border border-violet-500/30"
                : "text-muted-foreground hover:bg-accent"
            }`}
          >
            Copilot
          </button>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setInfoPanelOpen(!infoPanelOpen)}
            className={`rounded-lg p-2 transition-colors ${
              infoPanelOpen ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent"
            }`}
            title="Toggle info panel"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent"
            title="Settings"
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

      {copilotMode && (
        <div className="border-b border-violet-500/20 bg-violet-500/5 px-4 py-3">
          <div className="mx-auto max-w-2xl">
            <div className="mb-2 flex items-center gap-2">
              <svg className="h-4 w-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
              </svg>
              <span className="text-xs font-semibold text-violet-500">Copilot Mode</span>
              <span className="text-[10px] text-muted-foreground">
                Type a command or ask anything about your academics
              </span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={smartInput}
                onChange={(e) => setSmartInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSmartCommand();
                  }
                }}
                placeholder='e.g. "Plan my weekend", "What am I forgetting?", "I have football tonight"'
                className="flex-1 rounded-lg border bg-card px-3 py-2 text-sm outline-none transition-colors focus:border-violet-500/50"
                disabled={smartLoading}
              />
              <button
                type="button"
                onClick={handleSmartCommand}
                disabled={smartLoading || !smartInput.trim()}
                className="rounded-lg bg-violet-500 px-4 py-2 text-xs font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {smartLoading ? "Thinking..." : "Send"}
              </button>
            </div>
            {smartResult && (
              <div className="mt-2 rounded-lg border border-violet-500/20 bg-card/50 p-3 text-xs text-muted-foreground whitespace-pre-wrap">
                {smartResult}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 flex-shrink-0">
          <ConversationSidebar />
        </div>

        {showContext && dashboardData && (
          <div className="w-64 flex-shrink-0 border-r bg-card/50 p-4 overflow-y-auto">
            <h3 className="mb-3 text-xs font-semibold uppercase text-muted-foreground">Workspace Context</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs text-muted-foreground">Assignments</span>
                <p className="font-medium">{dashboardData.stats?.total || 0} total</p>
                <p className="text-xs text-muted-foreground">
                  {dashboardData.stats?.pending || 0} pending &middot; {dashboardData.stats?.overdue || 0} overdue
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Focus</span>
                <p className="font-medium">{dashboardData.stats?.completion_percentage || 0}% complete</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Subjects</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {(dashboardData.subjects || []).slice(0, 4).map((s: any) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px]"
                    >
                      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: s.color || "#6366f1" }} />
                      {s.name}
                    </span>
                  ))}
                </div>
              </div>
              <div className="pt-2 border-t">
                <p className="text-[10px] text-muted-foreground">
                  Context is auto-injected into prompts. No manual selection needed.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>

        <ConversationInfoPanel />
      </div>

      <AISettingsDialog />
    </div>
  );
}
