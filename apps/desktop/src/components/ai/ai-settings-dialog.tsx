import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAIStore } from "@/stores/ai-store";
import * as aiService from "@/lib/ai-service";

export function AISettingsDialog() {
  const { settingsOpen, setSettingsOpen, settings, setSettings } = useAIStore();

  const [temperature, setTemperature] = useState(settings?.temperature ?? 0.7);
  const [maxTokens, setMaxTokens] = useState(settings?.max_tokens ?? 2048);
  const [streaming, setStreaming] = useState(settings?.streaming_enabled ?? true);
  const [systemPrompt, setSystemPrompt] = useState(settings?.system_prompt ?? "");
  const [preferredProvider, setPreferredProvider] = useState(settings?.preferred_provider ?? "ollama");
  const [academicContext, setAcademicContext] = useState(settings?.academic_context ?? true);
  const [conversationMemory, setConversationMemory] = useState(settings?.conversation_memory ?? 10);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (settings) {
      setTemperature(settings.temperature);
      setMaxTokens(settings.max_tokens);
      setStreaming(settings.streaming_enabled);
      setSystemPrompt(settings.system_prompt ?? "");
      setPreferredProvider(settings.preferred_provider);
      setAcademicContext(settings.academic_context ?? true);
      setConversationMemory(settings.conversation_memory ?? 10);
    }
  }, [settings]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await aiService.updateAISettings({
        temperature,
        max_tokens: maxTokens,
        streaming_enabled: streaming,
        system_prompt: systemPrompt || null,
        preferred_provider: preferredProvider,
        academic_context: academicContext,
        conversation_memory: conversationMemory,
      });
      setSettings(updated);
      setSettingsOpen(false);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {settingsOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setSettingsOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border bg-card p-6 shadow-xl"
          >
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold">AI Settings</h2>
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="rounded p-1 text-muted-foreground hover:bg-accent"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-5">
              <div>
                <label className="mb-1.5 block text-sm font-medium">Preferred Provider</label>
                <select
                  value={preferredProvider}
                  onChange={(e) => setPreferredProvider(e.target.value)}
                  className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="ollama">Ollama (Local)</option>
                  <option value="gemini">Gemini (Google AI)</option>
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Temperature: {temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">Max Tokens</label>
                <input
                  type="number"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value) || 2048)}
                  min={128}
                  max={8192}
                  step={128}
                  className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Streaming Responses</label>
                <button
                  type="button"
                  role="switch"
                  aria-checked={streaming}
                  onClick={() => setStreaming(!streaming)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    streaming ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      streaming ? "translate-x-4.5" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Academic Context</label>
                  <p className="text-xs text-muted-foreground">Inject assignments & deadlines into prompts</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={academicContext}
                  onClick={() => setAcademicContext(!academicContext)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    academicContext ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      academicContext ? "translate-x-4.5" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Conversation Memory: {conversationMemory} messages
                </label>
                <input
                  type="range"
                  min={1}
                  max={50}
                  value={conversationMemory}
                  onChange={(e) => setConversationMemory(parseInt(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>1</span>
                  <span>50</span>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">System Prompt</label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={4}
                  className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Custom system prompt..."
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="rounded-lg border bg-secondary px-4 py-2 text-sm text-secondary-foreground hover:bg-secondary/80"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
