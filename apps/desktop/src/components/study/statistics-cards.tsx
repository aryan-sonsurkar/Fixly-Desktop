import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import type { StudyStatistics } from "@fixly/shared-types";

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
}

function AnimatedNumber({ value, duration = 1000, suffix = "", prefix = "", decimals = 0 }: AnimatedNumberProps) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef(0);
  const startTimeRef = useRef(0);

  useEffect(() => {
    startRef.current = 0;
    startTimeRef.current = 0;
    let animFrame: number;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(value * eased * Math.pow(10, decimals)) / Math.pow(10, decimals);
      setDisplay(current);
      if (progress < 1) {
        animFrame = requestAnimationFrame(animate);
      }
    };

    animFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animFrame);
  }, [value, duration, decimals]);

  return <span>{prefix}{display.toFixed(decimals)}{suffix}</span>;
}

interface StatCardProps {
  label: string;
  value: number;
  icon: string;
  color: string;
  suffix?: string;
  prefix?: string;
  decimals?: number;
}

function StatCard({ label, value, icon, color, suffix, prefix, decimals }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg border bg-card p-4 shadow-sm transition-shadow hover:shadow-md ${color}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-bold">
            <AnimatedNumber value={value} suffix={suffix} prefix={prefix} decimals={decimals} />
          </p>
        </div>
        <svg className="h-8 w-8 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
        </svg>
      </div>
    </motion.div>
  );
}

interface StatisticsCardsProps {
  statistics: StudyStatistics;
  isLoading?: boolean;
}

export function StatisticsCards({ statistics, isLoading }: StatisticsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  const cards: StatCardProps[] = [
    {
      label: "Current Streak",
      value: statistics.current_streak,
      suffix: " days",
      icon: "M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z",
      color: statistics.current_streak > 0 ? "border-l-4 border-l-orange-500" : "",
    },
    {
      label: "Longest Streak",
      value: statistics.longest_streak,
      suffix: " days",
      icon: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
      color: "border-l-4 border-l-yellow-500",
    },
    {
      label: "Study Points",
      value: statistics.total_study_points,
      icon: "M13 10V3L4 14h7v7l9-11h-7z",
      color: "border-l-4 border-l-purple-500",
    },
    {
      label: "Study Hours",
      value: statistics.total_study_hours,
      suffix: " hrs",
      decimals: 1,
      icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
      color: "border-l-4 border-l-blue-500",
    },
    {
      label: "Avg Daily Study",
      value: statistics.average_daily_study_minutes,
      suffix: " min",
      decimals: 1,
      icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
      color: "",
    },
    {
      label: "Assignments Finished",
      value: statistics.assignments_finished,
      icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
      color: "border-l-4 border-l-green-500",
    },
    {
      label: "Pomodoros Completed",
      value: statistics.pomodoros_completed,
      icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
      color: "border-l-4 border-l-red-500",
    },
    {
      label: "Study Days",
      value: statistics.total_study_days,
      suffix: " days",
      icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
      color: "",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
