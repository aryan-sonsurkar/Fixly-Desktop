import { useEffect, useRef, useCallback } from "react";
import { usePomodoroStore, TimerPhase } from "@/stores/pomodoro-store";

function notify(title: string, body: string, enabled: boolean) {
  if (enabled && "Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body, icon: "/icon.png" });
  }
}

export function usePomodoroTimer() {
  const {
    phase, timeRemaining, totalTime, cyclesCompleted, isRunning, settings,
    setPhase, setTimeRemaining, setTotalTime, setCyclesCompleted, setIsRunning,
    setSessionDialogOpen,
  } = usePomodoroStore();

  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const audioRef = useRef<HTMLAudioElement | undefined>(undefined);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const startTimestampRef = useRef<number>(0);

  useEffect(() => {
    audioRef.current = new Audio(
      "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAf39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f38=",
    );
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = undefined;
      }
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const playAlarm = useCallback(() => {
    if (audioRef.current && settings?.sound_enabled) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, [settings?.sound_enabled]);

  const switchPhase = useCallback(
    (nextPhase: TimerPhase, duration: number) => {
      setPhase(nextPhase);
      setTotalTime(duration);
      setTimeRemaining(duration);
      setIsRunning(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
    },
    [setPhase, setTotalTime, setTimeRemaining, setIsRunning],
  );

  const startTimer = useCallback(() => {
    if (timeRemaining <= 0 || isRunning) return;
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
    startTimestampRef.current = Date.now();
    setIsRunning(true);
  }, [timeRemaining, isRunning, setIsRunning]);

  const pauseTimer = useCallback(() => {
    setIsRunning(false);
    startTimestampRef.current = 0;
  }, [setIsRunning]);

  const resetTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = undefined;
    }
    setIsRunning(false);
    setTimeRemaining(totalTime);
    startTimestampRef.current = 0;
  }, [totalTime, setIsRunning, setTimeRemaining]);

  const skipPhase = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = undefined;
    }
    const s = usePomodoroStore.getState();
    setIsRunning(false);
    if (s.phase === "focus") {
      const nextCycles = s.cyclesCompleted + 1;
      setCyclesCompleted(nextCycles);
      const lbi = s.settings?.long_break_interval || 4;
      const isLongBreak = nextCycles % lbi === 0;
      if (isLongBreak) {
        const lbd = (s.settings?.long_break_duration || 15) * 60;
        switchPhase("long_break", lbd);
      } else {
        const sbd = (s.settings?.short_break_duration || 5) * 60;
        switchPhase("short_break", sbd);
      }
      notify("Focus Complete!", `Cycle ${nextCycles} finished. Time for a break!`, s.settings?.desktop_notifications ?? true);
    } else {
      setSessionDialogOpen(true);
      const fd = s.settings?.focus_duration || 25;
      switchPhase("focus", fd * 60);
    }
    startTimestampRef.current = 0;
  }, [setIsRunning, setCyclesCompleted, switchPhase, setSessionDialogOpen]);

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      return;
    }

    startTimestampRef.current = startTimestampRef.current || Date.now();

    intervalRef.current = setInterval(() => {
      const state = usePomodoroStore.getState();
      const elapsed = Math.floor((Date.now() - startTimestampRef.current) / 1000);
      const remaining = state.totalTime - elapsed;

      if (remaining <= 0) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
        setIsRunning(false);
        playAlarm();

        const s = usePomodoroStore.getState();
        const updatedCycles = s.cyclesCompleted;

        if (s.phase === "focus") {
          const newCycles = updatedCycles + 1;
          setCyclesCompleted(newCycles);
          notify("Focus Complete!", `Cycle ${newCycles} finished. Time for a break!`, s.settings?.desktop_notifications ?? true);

          const lbi = s.settings?.long_break_interval || 4;
          const isLongBreak = newCycles % lbi === 0;

          if (isLongBreak) {
            const lbd = (s.settings?.long_break_duration || 15) * 60;
            switchPhase("long_break", lbd);
          } else {
            const sbd = (s.settings?.short_break_duration || 5) * 60;
            switchPhase("short_break", sbd);
          }

          if (s.settings?.auto_start_breaks) {
            timeoutRef.current = setTimeout(() => usePomodoroStore.getState().setIsRunning(true), 500);
          }
        } else {
          setSessionDialogOpen(true);
          const fd = s.settings?.focus_duration || 25;
          switchPhase("focus", fd * 60);

          if (s.settings?.auto_start_focus) {
            timeoutRef.current = setTimeout(() => usePomodoroStore.getState().setIsRunning(true), 500);
          }
        }
        startTimestampRef.current = 0;
      } else {
        setTimeRemaining(remaining);
      }
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
    };
  }, [isRunning, playAlarm, setCyclesCompleted, setSessionDialogOpen, switchPhase, setIsRunning, setTimeRemaining]);

  const restartFromSettings = useCallback(
    (duration: number) => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = undefined;
      }
      setIsRunning(false);
      setPhase("focus");
      setTotalTime(duration);
      setTimeRemaining(duration);
      startTimestampRef.current = 0;
    },
    [setIsRunning, setPhase, setTotalTime, setTimeRemaining],
  );

  return {
    phase,
    timeRemaining,
    totalTime,
    cyclesCompleted,
    isRunning,
    settings,
    startTimer,
    pauseTimer,
    resetTimer,
    skipPhase,
    restartFromSettings,
  };
}
