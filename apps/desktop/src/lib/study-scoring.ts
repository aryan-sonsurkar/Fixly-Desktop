export const POINTS_WEIGHTS: Record<string, number> = {
  pomodoro: 10,
  assignment: 25,
  ai_study: 8,
  reading: 5,
  manual: 6,
  email: 3,
  ocr: 4,
  pdf_analysis: 7,
  quiz: 12,
  flashcard: 4,
  revision: 15,
};

export const DAILY_GOAL_POINTS_BONUS = 15;
export const DAILY_GOAL_THRESHOLD = 50;

export function getPointsForActivity(activityType: string): number {
  return POINTS_WEIGHTS[activityType] || 0;
}

export function calculateDailyGoalBonus(totalPoints: number): number {
  if (totalPoints >= DAILY_GOAL_THRESHOLD) {
    return DAILY_GOAL_POINTS_BONUS;
  }
  return 0;
}

export function getHeatmapColor(points: number): string {
  if (points === 0) return "bg-muted";
  if (points <= 25) return "bg-purple-300/40 dark:bg-purple-900/30";
  if (points <= 50) return "bg-purple-400/60 dark:bg-purple-800/50";
  if (points <= 100) return "bg-purple-500/80 dark:bg-purple-700/70";
  return "bg-purple-600 dark:bg-purple-500";
}

export function getHeatmapIntensity(points: number): number {
  if (points === 0) return 0;
  if (points <= 25) return 1;
  if (points <= 50) return 2;
  if (points <= 100) return 3;
  return 4;
}

export function calculateStreak(dates: string[]): { current: number; longest: number } {
  if (dates.length === 0) return { current: 0, longest: 0 };

  const sorted = [...new Set(dates)].sort().reverse();
  const today = new Date().toISOString().slice(0, 10);

  let current = 0;
  let checkDate = new Date(today + "T00:00:00Z");
  const checkStr = () => checkDate.toISOString().slice(0, 10);
  while (sorted.includes(checkStr())) {
    current++;
    checkDate.setUTCDate(checkDate.getUTCDate() - 1);
  }

  let longest = 0;
  let temp = 1;
  const ascending = [...sorted].reverse();
  for (let i = 1; i < ascending.length; i++) {
    const prev = new Date(ascending[i - 1] + "T00:00:00Z");
    const curr = new Date(ascending[i] + "T00:00:00Z");
    const diff = (curr.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24);
    if (diff === 1) {
      temp++;
    } else {
      longest = Math.max(longest, temp);
      temp = 1;
    }
  }
  longest = Math.max(longest, temp);

  return { current, longest };
}

export function generateCalendar(year: number): Array<{ date: string; dayOfWeek: number }> {
  const days: Array<{ date: string; dayOfWeek: number }> = [];
  const start = new Date(Date.UTC(year, 0, 1));
  const end = new Date(Date.UTC(year, 11, 31));

  const current = new Date(start);
  while (current <= end) {
    const dateStr = current.toISOString().slice(0, 10);
    days.push({
      date: dateStr,
      dayOfWeek: current.getUTCDay(),
    });
    current.setUTCDate(current.getUTCDate() + 1);
  }
  return days;
}
