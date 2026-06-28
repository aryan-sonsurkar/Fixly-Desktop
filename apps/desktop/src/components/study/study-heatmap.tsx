import { useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger, Button } from "@fixly/ui";
import type { CalendarDay } from "@fixly/shared-types";
import { getHeatmapColor } from "@/lib/study-scoring";

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface StudyHeatmapProps {
  days: CalendarDay[];
  year: number;
  onYearChange: (year: number) => void;
  onDayClick: (date: string) => void;
  isLoading?: boolean;
}

export function StudyHeatmap({ days, year, onYearChange, onDayClick, isLoading }: StudyHeatmapProps) {
  const daysMap = useMemo(() => {
    const map = new Map<string, CalendarDay>();
    for (const d of days) {
      map.set(d.date, d);
    }
    return map;
  }, [days]);

  const calendarCells = useMemo(() => {
    const cells: Array<{ date: string; dayOfWeek: number; points: number }> = [];
    const start = new Date(Date.UTC(year, 0, 1));
    const end = new Date(Date.UTC(year, 11, 31));
    const current = new Date(start);
    while (current <= end) {
      const dateStr = current.toISOString().slice(0, 10);
      const day = daysMap.get(dateStr);
      cells.push({
        date: dateStr,
        dayOfWeek: current.getUTCDay(),
        points: day?.study_points || 0,
      });
      current.setUTCDate(current.getUTCDate() + 1);
    }
    return cells;
  }, [daysMap, year]);

  const weeks = useMemo(() => {
    const result: Array<typeof calendarCells> = [];
    let currentWeek: typeof calendarCells = [];
    const firstDay = new Date(year, 0, 1).getDay();
    for (let i = 0; i < firstDay; i++) {
      currentWeek.push({ date: "", dayOfWeek: i, points: 0 });
    }
    for (const cell of calendarCells) {
      currentWeek.push(cell);
      if (currentWeek.length === 7) {
        result.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push({ date: "", dayOfWeek: currentWeek.length, points: 0 });
      }
      result.push(currentWeek);
    }
    return result;
  }, [calendarCells, year]);

  const monthLabels = useMemo(() => {
    const labels: Array<{ label: string; index: number }> = [];
    let monthSeen = -1;
    for (let i = 0; i < weeks.length; i++) {
      const firstValid = weeks[i].find((c) => c.date);
      if (firstValid) {
        const month = new Date(firstValid.date).getMonth();
        if (month !== monthSeen) {
          labels.push({ label: MONTH_LABELS[month], index: i });
          monthSeen = month;
        }
      }
    }
    return labels;
  }, [weeks]);

  const handlePrevYear = useCallback(() => onYearChange(year - 1), [year, onYearChange]);
  const handleNextYear = useCallback(() => onYearChange(year + 1), [year, onYearChange]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="flex gap-1">
          {Array.from({ length: 53 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1">
              {Array.from({ length: 7 }).map((_, j) => (
                <div key={j} className="h-3 w-3 animate-pulse rounded-sm bg-muted" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-muted-foreground">{year} Contributions</h3>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handlePrevYear}>&lt;</Button>
            <span className="min-w-[4rem] text-center text-sm font-medium">{year}</span>
            <Button variant="ghost" size="sm" onClick={handleNextYear}>&gt;</Button>
          </div>
        </div>

        <div className="overflow-x-auto pb-2">
          <div className="flex gap-0.5" style={{ minWidth: Math.max(weeks.length * 14, 600) }}>
            <div className="flex flex-col gap-0.5 pr-1">
              {WEEKDAY_LABELS.map((label) => (
                <div key={label} className="flex h-3 items-center text-[10px] text-muted-foreground">
                  {label}
                </div>
              ))}
            </div>
            <div className="relative flex gap-0.5">
              {monthLabels.map(({ label, index }) => (
                <div
                  key={label}
                  className="absolute -top-4 text-[10px] text-muted-foreground"
                  style={{ left: index * 14 }}
                >
                  {label}
                </div>
              ))}
              {weeks.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-0.5">
                  {week.map((cell, di) => {
                    if (!cell.date) {
                      return <div key={`empty-${wi}-${di}`} className="h-3 w-3" />;
                    }
                    return (
                      <Tooltip key={cell.date}>
                        <TooltipTrigger asChild>
                          <motion.button
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: (wi * 7 + di) * 0.001, duration: 0.2 }}
                            className={`h-3 w-3 cursor-pointer rounded-sm transition-colors ${getHeatmapColor(cell.points)}`}
                            onClick={() => onDayClick(cell.date)}
                          />
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs">
                          <p className="font-medium">{cell.date}</p>
                          <p>{cell.points} study points</p>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span>Less</span>
          <div className="h-3 w-3 rounded-sm bg-muted" />
          <div className="h-3 w-3 rounded-sm bg-purple-300/40 dark:bg-purple-900/30" />
          <div className="h-3 w-3 rounded-sm bg-purple-400/60 dark:bg-purple-800/50" />
          <div className="h-3 w-3 rounded-sm bg-purple-500/80 dark:bg-purple-700/70" />
          <div className="h-3 w-3 rounded-sm bg-purple-600 dark:bg-purple-500" />
          <span>More</span>
        </div>
      </div>
    </TooltipProvider>
  );
}
