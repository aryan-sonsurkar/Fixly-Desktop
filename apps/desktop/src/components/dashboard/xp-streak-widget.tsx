import { motion } from "framer-motion";

interface XPStreakWidgetProps {
  xp: number;
  streak: number;
}

export function XPStreakWidget({ xp, streak }: XPStreakWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-4">
        <div className="flex flex-col items-center">
          <svg className="mb-1 h-6 w-6 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <span className="text-xl font-bold">{xp}</span>
          <span className="text-[10px] text-muted-foreground">XP</span>
        </div>
        <div className="h-10 w-px bg-border" />
        <div className="flex flex-col items-center">
          <svg className="mb-1 h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          </svg>
          <span className="text-xl font-bold">{streak}</span>
          <span className="text-[10px] text-muted-foreground">day streak</span>
        </div>
      </div>
    </div>
  );
}

interface ProductivityScoreWidgetProps {
  score: number;
}

export function ProductivityScoreWidget({ score }: ProductivityScoreWidgetProps) {
  const color = score >= 80 ? "text-green-500" : score >= 60 ? "text-yellow-500" : "text-orange-500";
  const ringColor = score >= 80 ? "stroke-green-500" : score >= 60 ? "stroke-yellow-500" : "stroke-orange-500";
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <h3 className="mb-3 text-center text-sm font-semibold">Productivity Score</h3>
      <div className="flex justify-center">
        <svg width="88" height="88" className="shrink-0">
          <circle cx="44" cy="44" r="36" fill="none" stroke="currentColor" strokeWidth="6" className="text-muted/20" />
          <motion.circle
            cx="44" cy="44" r="36"
            fill="none"
            strokeWidth="6"
            strokeLinecap="round"
            className={ringColor}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
            transform="rotate(-90 44 44)"
          />
          <text x="44" y="44" textAnchor="middle" dominantBaseline="central" className={`fill-current text-2xl font-bold ${color}`}>
            {score}
          </text>
        </svg>
      </div>
    </div>
  );
}
