import { motion } from "framer-motion";
import { Skeleton } from "@fixly/ui";

interface MomentumWidgetProps {
  streak: number;
  weeklyHours: number;
  weeklyCycles: number;
  studyDays: number;
  loading: boolean;
}

export function MomentumWidget({ streak, weeklyHours, weeklyCycles, studyDays, loading }: MomentumWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <svg className="h-5 w-5 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
        <h3 className="text-sm font-semibold">Study Momentum</h3>
      </div>
      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 rounded-lg" />)}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-2 gap-3"
        >
          <div className="rounded-lg bg-violet-500/5 p-3">
            <span className="text-[10px] font-medium text-violet-500">Streak</span>
            <p className="mt-0.5 text-lg font-bold">{streak}d</p>
          </div>
          <div className="rounded-lg bg-cyan-500/5 p-3">
            <span className="text-[10px] font-medium text-cyan-500">This Week</span>
            <p className="mt-0.5 text-lg font-bold">{weeklyHours}h</p>
          </div>
          <div className="rounded-lg bg-amber-500/5 p-3">
            <span className="text-[10px] font-medium text-amber-500">Cycles</span>
            <p className="mt-0.5 text-lg font-bold">{weeklyCycles}</p>
          </div>
          <div className="rounded-lg bg-emerald-500/5 p-3">
            <span className="text-[10px] font-medium text-emerald-500">Study Days</span>
            <p className="mt-0.5 text-lg font-bold">{studyDays}/7</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
