import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Card, CardContent } from "@fixly/ui";
import { usePomodoroTimer } from "@/hooks/usePomodoroTimer";
import { usePomodoroStore } from "@/stores/pomodoro-store";
import { PomodoroTimer } from "@/components/pomodoro/pomodoro-timer";
import { PomodoroSettings } from "@/components/pomodoro/pomodoro-settings";
import { PomodoroAnalytics } from "@/components/pomodoro/pomodoro-analytics";
import { SessionDialog } from "@/components/pomodoro/session-dialog";
import {
  getPomodoroSettings,
  updatePomodoroSettings,
  getPomodoroAnalytics,
  completePomodoroSession,
} from "@/lib/pomodoro-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("pomodoro-page");

export function PomodoroPage() {
  const {
    phase, timeRemaining, totalTime, cyclesCompleted, isRunning,
    startTimer, pauseTimer, resetTimer, skipPhase, restartFromSettings,
  } = usePomodoroTimer();

  const {
    settings, analytics, settingsOpen, analyticsOpen, sessionDialogOpen,
    setSettings, setAnalytics, setSettingsOpen, setAnalyticsOpen, setSessionDialogOpen,
  } = usePomodoroStore();

  const { data: settingsData } = useQuery({
    queryKey: ["pomodoro-settings"],
    queryFn: getPomodoroSettings,
  });

  const { data: analyticsData } = useQuery({
    queryKey: ["pomodoro-analytics"],
    queryFn: getPomodoroAnalytics,
  });

  useEffect(() => {
    if (settingsData) {
      setSettings(settingsData);
      if (phase === "idle") {
        const s = usePomodoroStore.getState();
        s.setPhase("focus");
        s.setTotalTime(settingsData.focus_duration * 60);
        s.setTimeRemaining(settingsData.focus_duration * 60);
      }
    }
  }, [settingsData, phase, setSettings]);

  useEffect(() => {
    if (analyticsData) setAnalytics(analyticsData);
  }, [analyticsData, setAnalytics]);

  const handleSaveSettings = async (data: Record<string, unknown>) => {
    try {
      const updated = await updatePomodoroSettings(data as Parameters<typeof updatePomodoroSettings>[0]);
      setSettings(updated);
      const focusSeconds = (updated?.focus_duration ?? 25) * 60;
      restartFromSettings(focusSeconds);
    } catch (err) {
      logger.error("Failed to save settings", err);
    }
  };

  const handleSessionSubmit = async (data: {
    interruptions: number;
    notes: string;
    mood_after: string;
    tags: string[];
  }) => {
    try {
      const fd = settings?.focus_duration || 25;
      const bd = settings?.short_break_duration || 5;
      await completePomodoroSession({
        focus_duration: fd,
        break_duration: bd,
        cycles_completed: cyclesCompleted,
        total_focus_minutes: fd * cyclesCompleted,
        interruptions: data.interruptions,
        tags: data.tags,
        notes: data.notes || null,
        mood_after: data.mood_after,
        subject_id: null,
      });
    } catch (err) {
      logger.error("Failed to save session", err);
    }
  };

  return (
    <div className="mx-auto flex max-w-7xl items-start justify-center gap-6 p-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card>
          <CardContent className="flex flex-col items-center py-10">
            <PomodoroTimer
              phase={phase}
              timeRemaining={timeRemaining}
              totalTime={totalTime}
              cyclesCompleted={cyclesCompleted}
              isRunning={isRunning}
              onStart={startTimer}
              onPause={pauseTimer}
              onReset={resetTimer}
              onSkip={skipPhase}
              onSettingsOpen={() => setSettingsOpen(true)}
              onAnalyticsOpen={() => setAnalyticsOpen(true)}
            />
          </CardContent>
        </Card>
      </motion.div>

      <PomodoroSettings
        open={settingsOpen}
        settings={settings}
        onSave={handleSaveSettings}
        onClose={() => setSettingsOpen(false)}
      />

      <PomodoroAnalytics
        open={analyticsOpen}
        analytics={analytics}
        onClose={() => setAnalyticsOpen(false)}
      />

      <SessionDialog
        open={sessionDialogOpen}
        cyclesCompleted={cyclesCompleted}
        onSubmit={handleSessionSubmit}
        onClose={() => setSessionDialogOpen(false)}
      />
    </div>
  );
}
