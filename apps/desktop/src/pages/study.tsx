import { useEffect, useCallback, useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@fixly/ui";
import { StudyHeatmap } from "@/components/study/study-heatmap";
import { StudyDiary } from "@/components/study/study-diary";
import { StatisticsCards } from "@/components/study/statistics-cards";
import { useStudyStore } from "@/stores/study-store";
import {
  getCalendar,
  getDayDetail,
  getStudyStatistics,
  updateDay,
} from "@/lib/study-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("study-page");

export function StudyPage() {
  const {
    calendarYear, selectedDate, diaryOpen,
    setCalendar, setCalendarYear, setSelectedDay, setSelectedDate,
    setStatistics, setDiaryOpen,
    setIsLoadingCalendar, setIsLoadingDay, setIsLoadingStats,
  } = useStudyStore();
  const [isSaving, setIsSaving] = useState(false);
  const [diaryError, setDiaryError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const { data: calendarData, isLoading: calLoading } = useQuery({
    queryKey: ["study-calendar", calendarYear],
    queryFn: () => getCalendar(calendarYear),
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["study-statistics"],
    queryFn: getStudyStatistics,
  });

  const { data: dayData, isLoading: dayLoading } = useQuery({
    queryKey: ["study-day", selectedDate],
    queryFn: () => selectedDate ? getDayDetail(selectedDate) : Promise.resolve(null),
    enabled: !!selectedDate,
  });

  useEffect(() => {
    setIsLoadingCalendar(calLoading);
    if (calendarData) setCalendar(calendarData);
  }, [calendarData, calLoading, setCalendar, setIsLoadingCalendar]);

  useEffect(() => {
    setIsLoadingStats(statsLoading);
    if (statsData) setStatistics(statsData);
  }, [statsData, statsLoading, setStatistics, setIsLoadingStats]);

  useEffect(() => {
    setIsLoadingDay(!!dayLoading);
    if (dayData) setSelectedDay(dayData);
  }, [dayData, dayLoading, setSelectedDay, setIsLoadingDay]);

  const handleDayClick = useCallback((date: string) => {
    setSelectedDate(date);
    setDiaryOpen(true);
  }, [setSelectedDate, setDiaryOpen]);

  const handleDiarySave = useCallback(async (data: { mood?: string | null; productivity_rating?: number | null; notes?: string | null }) => {
    if (!selectedDate) return;
    setIsSaving(true);
    setDiaryError(null);
    try {
      await updateDay(selectedDate, data);
    } catch (err) {
      logger.error("Failed to save diary", err);
      if (mountedRef.current) setDiaryError("Failed to save diary entry. Please try again.");
    } finally {
      if (mountedRef.current) setIsSaving(false);
    }
  }, [selectedDate]);

  const handleYearChange = useCallback((year: number) => {
    setCalendarYear(year);
  }, [setCalendarYear]);

  const statistics = useStudyStore((s) => s.statistics);
  const selectedDay = useStudyStore((s) => s.selectedDay);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">Study Tracker</h1>
        <p className="text-sm text-muted-foreground">Track your consistency and study habits</p>
      </motion.div>

      <StatisticsCards statistics={statistics} isLoading={statsLoading} />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Study Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <StudyHeatmap
            days={calendarData?.days || []}
            year={calendarYear}
            onYearChange={handleYearChange}
            onDayClick={handleDayClick}
            isLoading={calLoading}
          />
        </CardContent>
      </Card>

      {diaryOpen && selectedDate && (
        <Card>
          <CardContent className="pt-6">
            {diaryError && (
              <div className="mb-4 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{diaryError}</div>
            )}
            {dayLoading ? (
              <div className="space-y-4">
                <div className="h-6 w-64 animate-pulse rounded bg-muted" />
                <div className="grid grid-cols-3 gap-4">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-16 animate-pulse rounded bg-muted" />
                  ))}
                </div>
              </div>
            ) : selectedDay ? (
              <StudyDiary
                day={selectedDay}
                onSave={handleDiarySave}
                onClose={() => setDiaryOpen(false)}
                isSaving={isSaving}
              />
            ) : (
              <p className="text-sm text-muted-foreground">No data for this day</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
