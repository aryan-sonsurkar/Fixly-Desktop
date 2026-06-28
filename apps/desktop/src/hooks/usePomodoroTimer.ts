import { useEffect, useRef, useCallback } from "react";
import { usePomodoroStore, TimerPhase } from "@/stores/pomodoro-store";

function notify(title: string, body: string) {
  if ("Notification" in window && Notification.permission === "granted") {
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

  useEffect(() => {
    audioRef.current = new Audio(
      "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAf39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f38=",
    );
    return () => {
      audioRef.current = undefined;
    };
  }, []);

  const playAlarm = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, []);

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
    setIsRunning(true);
  }, [timeRemaining, isRunning, setIsRunning]);

  const pauseTimer = useCallback(() => {
    setIsRunning(false);
  }, [setIsRunning]);

  const resetTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    setIsRunning(false);
    setTimeRemaining(totalTime);
  }, [totalTime, setIsRunning, setTimeRemaining]);

  const skipPhase = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    setTimeRemaining(0);
  }, [setTimeRemaining]);

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      const state = usePomodoroStore.getState();
      if (state.timeRemaining <= 1) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
        setIsRunning(false);
        playAlarm();

        const s = usePomodoroStore.getState();
        const updatedCycles = s.cyclesCompleted;

        if (s.phase === "focus") {
          const newCycles = updatedCycles + 1;
          setCyclesCompleted(newCycles);
          notify("Focus Complete!", `Cycle ${newCycles} finished. Time for a break!`);

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
            setTimeout(() => usePomodoroStore.getState().setIsRunning(true), 500);
          }
        } else {
          setSessionDialogOpen(true);
          const fd = s.settings?.focus_duration || 25;
          switchPhase("focus", fd * 60);

          if (s.settings?.auto_start_focus) {
            setTimeout(() => usePomodoroStore.getState().setIsRunning(true), 500);
          }
        }
      } else {
        setTimeRemaining(state.timeRemaining - 1);
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
      setIsRunning(false);
      setPhase("focus");
      setTotalTime(duration);
      setTimeRemaining(duration);
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
