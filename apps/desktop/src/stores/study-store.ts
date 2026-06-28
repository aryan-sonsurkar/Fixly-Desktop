import { create } from "zustand";
import type { CalendarDay, CalendarResponse, DayDetail, StudyStatistics, StudyStreak } from "@fixly/shared-types";

export interface StudyState {
  calendar: CalendarDay[];
  calendarYear: number;
  selectedDay: DayDetail | null;
  selectedDate: string | null;
  statistics: StudyStatistics | null;
  streak: StudyStreak | null;
  isLoadingCalendar: boolean;
  isLoadingDay: boolean;
  isLoadingStats: boolean;
  diaryOpen: boolean;

  setCalendar: (calendar: CalendarResponse) => void;
  setCalendarYear: (year: number) => void;
  setSelectedDay: (day: DayDetail | null) => void;
  setSelectedDate: (date: string | null) => void;
  setStatistics: (stats: StudyStatistics) => void;
  setStreak: (streak: StudyStreak) => void;
  setIsLoadingCalendar: (loading: boolean) => void;
  setIsLoadingDay: (loading: boolean) => void;
  setIsLoadingStats: (loading: boolean) => void;
  setDiaryOpen: (open: boolean) => void;
  reset: () => void;
}

const initialState = {
  calendar: [],
  calendarYear: new Date().getFullYear(),
  selectedDay: null,
  selectedDate: null,
  statistics: null,
  streak: null,
  isLoadingCalendar: false,
  isLoadingDay: false,
  isLoadingStats: false,
  diaryOpen: false,
};

export const useStudyStore = create<StudyState>((set) => ({
  ...initialState,

  setCalendar: (calendar) => set({ calendar: calendar.days, calendarYear: calendar.year }),
  setCalendarYear: (year) => set({ calendarYear: year }),
  setSelectedDay: (day) => set({ selectedDay: day }),
  setSelectedDate: (date) => set({ selectedDate: date }),
  setStatistics: (stats) => set({ statistics: stats }),
  setStreak: (streak) => set({ streak }),
  setIsLoadingCalendar: (loading) => set({ isLoadingCalendar: loading }),
  setIsLoadingDay: (loading) => set({ isLoadingDay: loading }),
  setIsLoadingStats: (loading) => set({ isLoadingStats: loading }),
  setDiaryOpen: (open) => set({ diaryOpen: open }),
  reset: () => set(initialState),
}));
