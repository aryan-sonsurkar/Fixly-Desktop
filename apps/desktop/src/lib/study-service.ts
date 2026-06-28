import apiClient from "@/lib/api-client";
import type { CalendarResponse, DayDetail, StudyStatistics, StudyStreak, StudySessionLog } from "@fixly/shared-types";

export interface LogSessionData {
  activity_type: string;
  duration_minutes?: number;
  subject_id?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateDayData {
  mood?: string | null;
  productivity_rating?: number | null;
  notes?: string | null;
}

export async function getCalendar(year?: number): Promise<CalendarResponse> {
  const params = year ? `?year=${year}` : "";
  const response = await apiClient.get(`/api/v1/study/calendar${params}`);
  return response.data;
}

export async function getDayDetail(date: string): Promise<DayDetail> {
  const response = await apiClient.get(`/api/v1/study/day/${date}`);
  return response.data;
}

export async function updateDay(date: string, data: UpdateDayData): Promise<DayDetail> {
  const response = await apiClient.put(`/api/v1/study/day/${date}`, data);
  return response.data;
}

export async function logSession(data: LogSessionData): Promise<StudySessionLog> {
  const response = await apiClient.post("/api/v1/study/session", data);
  return response.data;
}

export async function getStudyStatistics(): Promise<StudyStatistics> {
  const response = await apiClient.get("/api/v1/study/statistics");
  return response.data;
}

export async function getStudyStreak(): Promise<StudyStreak> {
  const response = await apiClient.get("/api/v1/study/streak");
  return response.data;
}
