import { motion } from "framer-motion";

const suggestions = [
  { icon: "📝", label: "Explain my assignment", prompt: "Can you help me understand my assignment and break it down into steps?" },
  { icon: "📚", label: "Help me study", prompt: "I need help studying for my upcoming exam. Can you create a study plan?" },
  { icon: "✍️", label: "Generate notes", prompt: "Can you help me generate concise study notes from my course material?" },
  { icon: "💻", label: "Solve coding problem", prompt: "I'm stuck on a coding problem. Can you help me understand the concept?" },
  { icon: "🔍", label: "Summarize concept", prompt: "Can you summarize this concept in simple terms?" },
  { icon: "📅", label: "Create revision plan", prompt: "I have exams coming up. Can you create a revision timetable for me?" },
];

interface WelcomeScreenProps {
  onSendPrompt: (prompt: string) => void;
}

export function WelcomeScreen({ onSendPrompt }: WelcomeScreenProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center gap-3 text-center"
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold">How can Fixly help you today?</h1>
        <p className="max-w-md text-sm text-muted-foreground">
          I&apos;m your AI academic assistant. I know your subjects, courses, and upcoming deadlines.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="grid w-full max-w-2xl grid-cols-2 gap-2.5"
      >
        {suggestions.map((s) => (
          <button
            key={s.label}
            type="button"
            onClick={() => onSendPrompt(s.prompt)}
            className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 text-left text-sm transition-all hover:bg-accent hover:shadow-sm"
          >
            <span className="text-lg">{s.icon}</span>
            <span className="font-medium">{s.label}</span>
          </button>
        ))}
      </motion.div>
    </div>
  );
}
