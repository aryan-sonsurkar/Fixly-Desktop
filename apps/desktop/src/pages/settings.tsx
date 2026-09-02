import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Button, Skeleton } from "@fixly/ui";
import { getMySettings, updateMySettings, getMyProfile } from "@/lib/profile-service";
import * as aiService from "@/lib/ai-service";
import { getDiagnostics, type Diagnostics } from "@/lib/diagnostics-service";
import { useUIStore } from "@/stores/ui-store";
import { useAuthContext } from "@/contexts/auth-context";
import { version } from "../../package.json";
import { createLogger } from "@/lib/logger";
import { toast } from "@/stores/toast-store";

const logger = createLogger("settings-page");

// ---- Theme helpers ----
const THEMES = [
  { value: "dark" as const, label: "Dark", desc: "Dark background" },
  { value: "light" as const, label: "Light", desc: "Bright background" },
  { value: "system" as const, label: "System", desc: "Follows OS setting" },
];

// ---- Section nav ----
type Section = "appearance" | "notifications" | "ai" | "account" | "about";
const SECTIONS: { id: Section; label: string; icon: string }[] = [
  { id: "appearance", label: "Appearance", icon: "M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" },
  { id: "notifications", label: "Notifications", icon: "M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" },
  { id: "ai", label: "AI", icon: "M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" },
  { id: "account", label: "Account", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
  { id: "about", label: "About", icon: "M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" },
];

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { theme: uiTheme, setTheme: setUiTheme } = useUIStore();
  const { user } = useAuthContext();
  const [activeSection, setActiveSection] = useState<Section>("appearance");

  // ---- Profile + Settings queries ----
  const { data: settings, isLoading: settingsLoading, isError: settingsError } = useQuery({
    queryKey: ["settings"],
    queryFn: getMySettings,
    staleTime: 60 * 1000,
    placeholderData: (prev) => prev,
  });
  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: getMyProfile,
    staleTime: 60 * 1000,
    placeholderData: (prev) => prev,
  });

  // ---- Local notification toggles ----
  const [notifEnabled, setNotifEnabled] = useState(true);
  const [assignmentReminders, setAssignmentReminders] = useState(true);
  useEffect(() => {
    if (settings) {
      setNotifEnabled(settings.notification_enabled ?? true);
      setAssignmentReminders(settings.assignment_reminders ?? true);
    }
  }, [settings]);

  const notifMut = useMutation({
    mutationFn: (data: { notification_enabled?: boolean; assignment_reminders?: boolean }) =>
      updateMySettings(data),
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
      toast({ type: "success", title: "Notification settings saved" });
    },
    onError: (err) => {
      logger.error("Failed to save notification settings", err);
      toast({ type: "error", title: "Failed to save" });
    },
  });

  // ---- Theme handler (Bug 9 fix: wire to ui-store + persist) ----
  const handleThemeChange = (val: "dark" | "light" | "system") => {
    setUiTheme(val);
    // Also persist to backend so it survives session restore
    void updateMySettings({ theme: val }).catch((e) => logger.warn("Theme persist failed", e));
  };

  void settings; // theme sync handled via handleThemeChange; backend as source of truth on next login

  // ---- AI state (Bug 10) ----
  const [aiProvider, setAiProvider] = useState("auto");
  const [aiTemp, setAiTemp] = useState(0.7);
  const [aiStreaming, setAiStreaming] = useState(true);
  const [aiDetail, setAiDetail] = useState<aiService.ProviderDetailResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSaving, setAiSaving] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const { data: aiSettings } = useQuery({
    queryKey: ["ai-settings"],
    queryFn: aiService.getAISettings,
    staleTime: 30 * 1000,
    placeholderData: (prev) => prev,
  });

  useEffect(() => {
    if (aiSettings) {
      setAiProvider(aiSettings.preferred_provider ?? "auto");
      setAiTemp(aiSettings.temperature ?? 0.7);
      setAiStreaming(aiSettings.streaming_enabled ?? true);
    }
  }, [aiSettings]);

  const fetchAiDetail = async () => {
    setAiLoading(true);
    try {
      const d = await aiService.checkProviderDetail();
      setAiDetail(d);
    } catch {
      setAiDetail(null);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    if (activeSection === "ai") {
      void fetchAiDetail();
    }
  }, [activeSection]);

  const handleAiSave = async () => {
    setAiSaving(true);
    setAiError(null);
    try {
      const modelToSave = aiProvider === "fixly-local" ? "qwen2-0.5b-instruct-q4_k_m.gguf" : null;
      const updated = await aiService.updateAISettings({
        preferred_provider: aiProvider,
        provider_model: modelToSave,
        temperature: aiTemp,
        streaming_enabled: aiStreaming,
      });
      queryClient.setQueryData(["ai-settings"], updated);
      toast({ type: "success", title: "AI settings saved" });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not save AI settings";
      setAiError(msg);
      toast({ type: "error", title: msg });
    } finally {
      setAiSaving(false);
    }
  };

  // ---- Diagnostics for About ----
  const [diag, setDiag] = useState<Diagnostics | null>(null);
  const [diagLoading, setDiagLoading] = useState(false);
  useEffect(() => {
    if (activeSection === "about") {
      setDiagLoading(true);
      getDiagnostics()
        .then(setDiag)
        .catch(() => setDiag(null))
        .finally(() => setDiagLoading(false));
    }
  }, [activeSection]);

  if (settingsLoading && !settings) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <Skeleton className="mb-6 h-8 w-40" />
        <div className="grid grid-cols-4 gap-6">
          <Skeleton className="h-64 rounded-xl" />
          <div className="col-span-3 space-y-4">
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (settingsError && !settings) {
    return (
      <div className="mx-auto max-w-5xl p-6 text-center">
        <p className="text-sm text-destructive">Failed to load settings.</p>
        <Button size="sm" className="mt-3" onClick={() => queryClient.invalidateQueries({ queryKey: ["settings"] })}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your Fixly experience, AI, and account</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[200px_1fr]">
        {/* Sidebar nav */}
        <nav className="flex flex-row gap-1 overflow-x-auto lg:flex-col lg:overflow-visible" aria-label="Settings sections">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveSection(s.id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeSection === s.id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`}
            >
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={s.icon} />
              </svg>
              {s.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="min-w-0 space-y-6">
          {/* Appearance */}
          {activeSection === "appearance" && (
            <motion.section
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border bg-card p-6"
            >
              <h2 className="text-base font-semibold">Appearance</h2>
              <p className="mb-4 text-sm text-muted-foreground">Choose how Fixly looks on this device. Changes apply immediately.</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {THEMES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => handleThemeChange(t.value)}
                    className={`flex flex-col items-start gap-1 rounded-xl border-2 p-4 text-left transition-colors ${
                      uiTheme === t.value ? "border-primary bg-primary/5" : "border-border hover:border-primary/40 hover:bg-accent/50"
                    }`}
                  >
                    <span className="text-sm font-medium capitalize">{t.label}</span>
                    <span className="text-xs text-muted-foreground">{t.desc}</span>
                    {uiTheme === t.value && (
                      <span className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-primary">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Active
                      </span>
                    )}
                  </button>
                ))}
              </div>
              {uiTheme === "system" && (
                <p className="mt-3 text-xs text-muted-foreground">System theme follows your operating system preference and updates automatically.</p>
              )}
            </motion.section>
          )}

          {/* Notifications */}
          {activeSection === "notifications" && (
            <motion.section
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border bg-card p-6"
            >
              <h2 className="text-base font-semibold">Notifications</h2>
              <p className="mb-5 text-sm text-muted-foreground">Control how Fixly notifies you about assignments and activity.</p>
              <div className="space-y-4">
                <label className="flex cursor-pointer items-center justify-between rounded-lg border p-4 hover:bg-accent/30">
                  <div>
                    <p className="text-sm font-medium">Enable notifications</p>
                    <p className="text-xs text-muted-foreground">Receive in-app notifications</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifEnabled}
                    onChange={(e) => {
                      const v = e.target.checked;
                      setNotifEnabled(v);
                      notifMut.mutate({ notification_enabled: v });
                    }}
                    className="h-4 w-4 accent-primary"
                  />
                </label>
                <label className="flex cursor-pointer items-center justify-between rounded-lg border p-4 hover:bg-accent/30">
                  <div>
                    <p className="text-sm font-medium">Assignment reminders</p>
                    <p className="text-xs text-muted-foreground">Get notified before deadlines</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={assignmentReminders}
                    onChange={(e) => {
                      const v = e.target.checked;
                      setAssignmentReminders(v);
                      notifMut.mutate({ assignment_reminders: v });
                    }}
                    className="h-4 w-4 accent-primary"
                  />
                </label>
              </div>
            </motion.section>
          )}

          {/* AI */}
          {activeSection === "ai" && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <section className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold">AI Provider</h2>
                <p className="mb-4 text-sm text-muted-foreground">Choose which AI powers Fixly AI. Auto tries Fixly Local first.</p>

                {/* Provider status — only Fixly AI */}
                {aiLoading ? (
                  <div className="mb-4">
                    <Skeleton className="h-20 w-full rounded-lg" />
                  </div>
                ) : aiDetail ? (
                  <div className="mb-4">
                    {(() => {
                      const fixly = aiDetail.providers["fixly-local"];
                      return (
                        <div className={`rounded-lg border p-3 ${fixly?.available ? "border-green-500/30 bg-green-500/5" : "border-amber-500/20 bg-amber-500/5"}`}>
                          <div className="flex items-center gap-2">
                            <span className={`h-2 w-2 rounded-full ${fixly?.available ? "bg-green-500" : "bg-amber-500"}`} />
                            <span className="text-xs font-semibold">Fixly AI</span>
                            <span className="ml-auto text-[10px] text-muted-foreground">Qwen2 0.5B · Offline · Bundled</span>
                          </div>
                          <p className="mt-1 text-[11px] text-muted-foreground">
                            {fixly?.available ? "Ready — no download needed, runs entirely offline" : fixly?.error || "Model not found — reinstall Fixly 1.0.0+ installer"}
                          </p>
                        </div>
                      );
                    })()}
                  </div>
                ) : null}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium">AI Provider</label>
                    <div className="w-full rounded-lg border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">Fixly AI — Bundled (Qwen2 0.5B)</div>
                    <p className="mt-1 text-[10px] text-muted-foreground">Offline, private, no setup needed.</p>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-medium">Model</label>
                    <div className="rounded-lg border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
                      qwen2-0.5b-instruct-q4_k_m.gguf — bundled
                    </div>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium">Temperature: {aiTemp.toFixed(1)}</label>
                    <input
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      value={aiTemp}
                      onChange={(e) => setAiTemp(parseFloat(e.target.value))}
                      className="w-full accent-primary"
                    />
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>
                  <label className="flex items-center justify-between rounded-lg border p-3">
                    <span className="text-sm font-medium">Streaming responses</span>
                    <input type="checkbox" checked={aiStreaming} onChange={(e) => setAiStreaming(e.target.checked)} className="h-4 w-4 accent-primary" />
                  </label>
                </div>

                {aiError && <p className="mt-3 text-xs text-destructive">{aiError}</p>}

                <div className="mt-4 flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => void fetchAiDetail()} disabled={aiLoading}>
                    Test Connection
                  </Button>
                  <Button size="sm" onClick={handleAiSave} disabled={aiSaving}>
                    {aiSaving ? "Saving..." : "Save AI Settings"}
                  </Button>
                </div>
              </section>
            </motion.div>
          )}

          {/* Account */}
          {activeSection === "account" && (
            <motion.section
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border bg-card p-6"
            >
              <h2 className="text-base font-semibold">Account</h2>
              <p className="mb-5 text-sm text-muted-foreground">Your Fixly account and profile.</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="text-sm font-medium">{user?.email || profile?.email || "—"}</p>
                </div>
                <div className="rounded-lg border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">Name</p>
                  <p className="text-sm font-medium">{profile?.full_name || profile?.display_name || user?.profile?.full_name || "—"}</p>
                </div>
                <div className="rounded-lg border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">XP</p>
                  <p className="text-sm font-medium">{profile?.xp ?? user?.profile?.xp ?? 0}</p>
                </div>
                <div className="rounded-lg border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">Streak</p>
                  <p className="text-sm font-medium">{profile?.streak ?? user?.profile?.streak ?? 0} days</p>
                </div>
                {profile?.education_type && (
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Education</p>
                    <p className="text-sm font-medium">
                      {[profile.education_type, profile.education_year, profile.branch_stream, profile.college_name].filter(Boolean).join(" · ") || "—"}
                    </p>
                  </div>
                )}
              </div>
              {profile?.email && (
                <p className="mt-4 text-xs text-muted-foreground">
                  Manage your profile details from the Profile page. Password changes require email verification.
                </p>
              )}
            </motion.section>
          )}

          {/* About */}
          {activeSection === "about" && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <section className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold">About Fixly</h2>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Version</p>
                    <p className="text-sm font-mono font-medium">{version}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Build</p>
                    <p className="text-sm font-mono font-medium">{import.meta.env.VITE_BUILD_VERSION || version}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Environment</p>
                    <p className="text-sm font-medium">{import.meta.env.DEV ? "Development" : "Production"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Platform</p>
                    <p className="text-sm font-medium">{navigator.platform || "Desktop"}</p>
                  </div>
                </div>
              </section>

              <section className="rounded-xl border bg-card p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold">Diagnostics</h2>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={diagLoading}
                    onClick={() => {
                      setDiagLoading(true);
                      getDiagnostics()
                        .then(setDiag)
                        .finally(() => setDiagLoading(false));
                    }}
                  >
                    {diagLoading ? "Checking..." : "Run Diagnostics"}
                  </Button>
                </div>
                {!diag && !diagLoading && <p className="text-sm text-muted-foreground">Click Run Diagnostics to check backend, database, and AI health.</p>}
                {diagLoading && (
                  <div className="space-y-2">
                    <Skeleton className="h-10 w-full rounded-lg" />
                    <Skeleton className="h-10 w-full rounded-lg" />
                  </div>
                )}
                {diag && !diagLoading && (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      { label: "Backend", data: diag.backend },
                      { label: "Supabase", data: diag.supabase },
                      { label: "AI", data: diag.ai },
                      { label: "Database", data: diag.database },
                    ].map((row) => (
                      <div key={row.label} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                        <span className="font-medium">{row.label}</span>
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            row.data.status === "healthy"
                              ? "bg-green-500/10 text-green-600"
                              : row.data.status === "unconfigured"
                                ? "bg-amber-500/10 text-amber-600"
                                : "bg-red-500/10 text-red-600"
                          }`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${row.data.status === "healthy" ? "bg-green-500" : row.data.status === "unconfigured" ? "bg-amber-500" : "bg-red-500"}`} />
                          {row.data.status}
                        </span>
                      </div>
                    ))}
                    {diag.ai.error && <p className="col-span-2 text-xs text-muted-foreground">AI: {diag.ai.error}</p>}
                    {diag.backend.error && <p className="col-span-2 text-xs text-destructive">Backend: {diag.backend.error}</p>}
                  </div>
                )}
              </section>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
