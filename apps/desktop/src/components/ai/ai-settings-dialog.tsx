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
  const [preferredProvider, setPreferredProvider] = useState(settings?.preferred_provider ?? "auto");
  const [providerModel, setProviderModel] = useState(settings?.provider_model ?? "");
  const [academicContext, setAcademicContext] = useState(settings?.academic_context ?? true);
  const [conversationMemory, setConversationMemory] = useState(settings?.conversation_memory ?? 10);
  const [saving, setSaving] = useState(false);

  const [ollamaStatus, setOllamaStatus] = useState<aiService.ProviderDetail | null>(null);
  const [fixlyStatus, setFixlyStatus] = useState<aiService.ProviderDetail | null>(null);
  const [testing, setTesting] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (settings) {
      setTemperature(settings.temperature);
      setMaxTokens(settings.max_tokens);
      setStreaming(settings.streaming_enabled);
      setSystemPrompt(settings.system_prompt ?? "");
      setPreferredProvider(settings.preferred_provider);
      setProviderModel(settings.provider_model ?? "");
      setAcademicContext(settings.academic_context ?? true);
      setConversationMemory(settings.conversation_memory ?? 10);
    }
  }, [settings]);

  useEffect(() => {
    if (settingsOpen) {
      void fetchOllamaStatus();
      void loadModels();
    }
  }, [settingsOpen]);

  const fetchOllamaStatus = async () => {
    try {
      const detail = await aiService.checkProviderDetail();
      const ollama = detail.providers.ollama;
      const fixly = detail.providers["fixly-local"];
      setOllamaStatus(ollama);
      if (fixly) setFixlyStatus(fixly);
      // Prefer Fixly Local models if available, else Ollama
      const models = fixly?.models?.length ? fixly.models : ollama?.models || [];
      if (models.length) {
        setAvailableModels(models);
        if (!settings?.provider_model) {
          const sel = fixly?.models?.[0] || ollama?.models?.[0];
          if (sel) setProviderModel(sel);
        }
      }
    } catch {
      setOllamaStatus({
        name: "ollama",
        available: false,
        installed: false,
        running: false,
        model_count: 0,
        models: [],
        error: "Could not reach backend",
      });
      setFixlyStatus(null);
      setAvailableModels([]);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      await fetchOllamaStatus();
    } finally {
      setTesting(false);
    }
  };

  const loadModels = async () => {
    setLoadingModels(true);
    setModelError(null);
    try {
      const models = await aiService.listOllamaModels(true);
      const names = models.map((m) => m.name);
      setAvailableModels(names);
      setOllamaStatus((current) => current ? {
        ...current,
        models: names,
        model_count: names.length,
        available: current.running && names.length > 0,
        error: current.running && names.length === 0 ? "No models installed. Install an Ollama model to use Fixly AI." : current.error,
      } : current);
      if (!providerModel && names.length > 0) {
        setProviderModel(names[0]);
      }
    } catch (error) {
      setAvailableModels([]);
      setModelError(error instanceof Error ? error.message : "Could not load Ollama models.");
    } finally {
      setLoadingModels(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const modelToSave = preferredProvider === "fixly-local" ? "qwen2-0.5b-instruct-q4_k_m.gguf" : (preferredProvider === "ollama" ? (providerModel || null) : null);
      const updated = await aiService.updateAISettings({
        temperature,
        max_tokens: maxTokens,
        streaming_enabled: streaming,
        system_prompt: systemPrompt || null,
        preferred_provider: preferredProvider,
        provider_model: modelToSave,
        academic_context: academicContext,
        conversation_memory: conversationMemory,
      });
      setSettings(updated);
      setSettingsOpen(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Could not save AI settings.");
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

            {/* Fixly Local - Bundled */}
            <div className="mb-3 rounded-lg border bg-primary/5 p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Fixly AI (Local)</span>
                  {fixlyStatus ? (
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${fixlyStatus.available ? "bg-green-500/10 text-green-600" : "bg-amber-500/10 text-amber-600"}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${fixlyStatus.available ? "bg-green-500" : "bg-amber-500"}`} />
                      {fixlyStatus.available ? "Ready" : "Not ready"}
                    </span>
                  ) : (
                    <span className="text-[10px] text-muted-foreground">Checking...</span>
                  )}
                </div>
                <span className="text-[11px] text-muted-foreground">Qwen2 0.5B • Bundled • Offline</span>
              </div>
              {fixlyStatus?.error && <p className="mt-1.5 text-[11px] text-amber-600">{fixlyStatus.error}</p>}
              {fixlyStatus?.available && <p className="mt-1 text-[11px] text-muted-foreground">1 model bundled • No download needed</p>}
            </div>
            {/* Ollama */}
            <div className="mb-5 rounded-lg border bg-card p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Ollama Connection</span>
                  {ollamaStatus ? (
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        ollamaStatus.running
                          ? "bg-green-500/10 text-green-600"
                          : "bg-red-500/10 text-red-600"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          ollamaStatus.running ? "bg-green-500" : "bg-red-500"
                        }`}
                      />
                      {ollamaStatus.running ? "Running" : "Not running"}
                    </span>
                  ) : (
                    <span className="text-[10px] text-muted-foreground">Checking...</span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="rounded-lg border px-3 py-1 text-xs transition-colors hover:bg-accent disabled:opacity-50"
                >
                  {testing ? "Testing..." : "Test Connection"}
                </button>
              </div>
              {ollamaStatus && ollamaStatus.error && (
                <p className="mt-1.5 text-[11px] text-red-500">{ollamaStatus.error}</p>
              )}
              {ollamaStatus && ollamaStatus.running && availableModels.length > 0 && (
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {ollamaStatus.model_count} model{ollamaStatus.model_count !== 1 ? "s" : ""} available
                </p>
              )}
            </div>

            <div className="space-y-5">
              <div>
                <label className="mb-1.5 block text-sm font-medium">Preferred Provider</label>
                <select
                  value={preferredProvider}
                  onChange={(e) => setPreferredProvider(e.target.value)}
                  className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="auto">Auto (Fixly Local first)</option>
                  <option value="fixly-local">Fixly AI (Local - Bundled Qwen2 0.5B)</option>
                  <option value="ollama">Ollama (Local)</option>
                  <option value="gemini">Gemini (Google AI)</option>
                </select>
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="text-sm font-medium">Model {preferredProvider === "fixly-local" && <span className="text-xs text-muted-foreground font-normal">(bundled)</span>}</label>
                  <button
                    type="button"
                    onClick={loadModels}
                    disabled={loadingModels}
                    className="text-[10px] text-muted-foreground underline hover:text-foreground disabled:opacity-50"
                  >
                    {loadingModels ? "Loading..." : "Refresh models"}
                  </button>
                </div>
                {preferredProvider === "fixly-local" ? (
                  <div className="w-full rounded-lg border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">qwen2-0.5b-instruct-q4_k_m.gguf � bundled, no download</div>
                ) : (
                  <select
                    value={providerModel}
                    onChange={(e) => setProviderModel(e.target.value)}
                    disabled={loadingModels || availableModels.length === 0}
                    className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  >
                    {availableModels.length === 0 && <option value="">Install an Ollama model to use Fixly AI.</option>}
                    {providerModel && !availableModels.includes(providerModel) && (
                      <option value={providerModel}>Selected model is no longer installed.</option>
                    )}
                    {availableModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                )}
                {modelError && <p className="mt-1 text-[11px] text-red-500">{modelError}</p>}
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










            </div>

            <div className="mt-6 flex justify-end gap-3">
              {saveError && <p className="mr-auto self-center text-xs text-red-500">{saveError}</p>}
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
