import { motion } from "framer-motion";
import { Button } from "@fixly/ui";
import { cn } from "@fixly/shared-utils";
import { TimerPhase } from "@/stores/pomodoro-store";

interface PomodoroTimerProps {
  phase: TimerPhase;
  timeRemaining: number;
  totalTime: number;
  cyclesCompleted: number;
  isRunning: boolean;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onSkip: () => void;
  onSettingsOpen: () => void;
  onAnalyticsOpen: () => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

const phaseLabels: Record<TimerPhase, string> = {
  idle: "Focus",
  focus: "Focus",
  short_break: "Short Break",
  long_break: "Long Break",
};

const phaseColors: Record<TimerPhase, string> = {
  idle: "text-red-500",
  focus: "text-red-500",
  short_break: "text-green-500",
  long_break: "text-blue-500",
};

export function PomodoroTimer({
  phase,
  timeRemaining,
  totalTime,
  cyclesCompleted,
  isRunning,
  onStart,
  onPause,
  onReset,
  onSkip,
  onSettingsOpen,
  onAnalyticsOpen,
}: PomodoroTimerProps) {
  const progress = totalTime > 0 ? 1 - timeRemaining / totalTime : 0;
  const circumference = 2 * Math.PI * 120;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onAnalyticsOpen}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </Button>
        <span className="text-xs text-muted-foreground">
          Cycle {cyclesCompleted + 1}
        </span>
        <Button variant="ghost" size="sm" onClick={onSettingsOpen}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </Button>
      </div>

      <div className="relative flex items-center justify-center">
        <svg className="-rotate-90" width="280" height="280" viewBox="0 0 280 280">
          <circle cx="140" cy="140" r="120" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/20" />
          <motion.circle
            cx="140" cy="140" r="120" fill="none" stroke="currentColor" strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={cn("transition-colors", phaseColors[phase])}
            initial={false}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "linear" }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <motion.span
            key={phase}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-xs font-medium text-muted-foreground uppercase tracking-wider"
          >
            {phaseLabels[phase]}
          </motion.span>
          <span className="text-6xl font-bold tabular-nums tracking-tight">
            {formatTime(timeRemaining)}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {!isRunning ? (
          <Button size="lg" className="min-w-[120px]" onClick={onStart} disabled={timeRemaining <= 0 && phase !== "idle"}>
            {phase === "idle" ? "Start Focus" : "Resume"}
          </Button>
        ) : (
          <Button size="lg" variant="outline" className="min-w-[120px]" onClick={onPause}>
            Pause
          </Button>
        )}
        {phase !== "idle" && (
          <>
            <Button variant="outline" size="lg" onClick={onReset}>Reset</Button>
            <Button variant="ghost" size="lg" onClick={onSkip}>Skip</Button>
          </>
        )}
      </div>
    </div>
  );
}
