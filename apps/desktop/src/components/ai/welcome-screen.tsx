import { motion } from "framer-motion";

const suggestions = [
  { icon: "assignment", label: "Explain my assignment", prompt: "Can you help me understand my assignment and break it down into steps?", desc: "Break down requirements" },
  { icon: "study", label: "Help me study", prompt: "I need help studying for my upcoming exam. Can you create a study plan?", desc: "Personalized plan" },
  { icon: "notes", label: "Generate notes", prompt: "Can you help me generate concise study notes from my course material?", desc: "Concise summaries" },
  { icon: "code", label: "Solve coding problem", prompt: "I'm stuck on a coding problem. Can you help me understand the concept?", desc: "Step-by-step help" },
  { icon: "search", label: "Summarize concept", prompt: "Can you summarize this concept in simple terms?", desc: "Simple explanations" },
  { icon: "plan", label: "Create revision plan", prompt: "I have exams coming up. Can you create a revision timetable for me?", desc: "Exam timetable" },
];

function SuggestIcon({ type }: { type: string }) {
  const cls = "h-5 w-5 text-primary";
  switch (type) {
    case "assignment":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M9 5a2 2 0 012 2h2a2 2 0 01-2 2H9a2 2 0 01-2-2V7a2 2 0 012-2z M9 12h6M9 16h6" /></svg>;
    case "study":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>;
    case "notes":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M11 5a2 2 0 012 2v2a2 2 0 01-2 2H9a2 2 0 01-2-2V7a2 2 0 012-2h2z" /></svg>;
    case "code":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8 12l-3 3 3 3M16 12l3 3-3 3M14 8l-2 8" /></svg>;
    case "search":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 110-16 8 8 0 010 16z" /></svg>;
    default:
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3M3 11h18M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>;
  }
}

interface WelcomeScreenProps {
  onSendPrompt: (prompt: string) => void;
}

export function WelcomeScreen({ onSendPrompt }: WelcomeScreenProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 p-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col items-center gap-3 text-center"
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-violet-500/20 ring-1 ring-primary/20">
          <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">How can Fixly help you today?</h1>
        <p className="max-w-md text-sm text-muted-foreground">
          I&apos;m your AI academic assistant. I know your subjects, courses, and upcoming deadlines.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12, duration: 0.4 }}
        className="grid w-full max-w-2xl grid-cols-1 gap-2.5 sm:grid-cols-2"
      >
        {suggestions.map((s, i) => (
          <motion.button
            key={s.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.18 + i * 0.04 }}
            type="button"
            onClick={() => onSendPrompt(s.prompt)}
            className="group flex items-center gap-3 rounded-xl border bg-card px-4 py-3.5 text-left transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-accent/50 hover:shadow-md"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/15 transition-colors">
              <SuggestIcon type={s.icon} />
            </span>
            <span className="flex flex-col">
              <span className="text-sm font-medium leading-none">{s.label}</span>
              <span className="text-xs text-muted-foreground">{s.desc}</span>
            </span>
          </motion.button>
        ))}
      </motion.div>
      <p className="text-xs text-muted-foreground">Try a prompt or type your own message below</p>
    </div>
  );
}
