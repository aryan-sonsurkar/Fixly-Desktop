import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Button, Input, Label } from "@fixly/ui";
import { useAuthContext } from "@/contexts/auth-context";
import { completeOnboarding } from "@/lib/profile-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("onboarding-page");

const EDUCATION_TYPES = [
  { value: "diploma", label: "Diploma" },
  { value: "degree", label: "Degree" },
  { value: "junior_college", label: "Junior College" },
  { value: "senior_secondary", label: "Senior Secondary" },
  { value: "commerce", label: "Commerce" },
  { value: "arts", label: "Arts" },
  { value: "science", label: "Science" },
] as const;

const EDUCATION_YEARS: Record<string, string[]> = {
  diploma: ["First Year", "Second Year", "Third Year"],
  degree: ["First", "Second", "Third", "Fourth Year"],
  junior_college: ["11th", "12th"],
  senior_secondary: ["9th", "10th"],
  commerce: ["First Year", "Second Year", "Third Year"],
  arts: ["First Year", "Second Year", "Third Year"],
  science: ["First Year", "Second Year", "Third Year"],
};

const SUBJECT_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
  "#06b6d4", "#d946ef", "#e11d48", "#0ea5e9", "#65a30d",
];

const STEPS = ["Personal", "Academic", "Institution", "Preferences", "Subjects"];

const personalSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  display_name: z.string().optional(),
});

const academicSchema = z.object({
  education_type: z.string().min(1, "Select your education type"),
  education_year: z.string().min(1, "Select your year"),
});

const institutionSchema = z.object({
  college_name: z.string().min(1, "College name is required"),
  university_board: z.string().min(1, "University/Board is required"),
  branch_stream: z.string().min(1, "Branch/Stream is required"),
  division: z.string().optional(),
  roll_number: z.string().optional(),
});

const preferencesSchema = z.object({
  theme: z.enum(["dark", "light", "system"]),
  daily_goal_hours: z.coerce.number().min(0).max(24),
  pomodoro_focus: z.coerce.number().min(1).max(120),
  pomodoro_break: z.coerce.number().min(1).max(60),
  assignment_reminders: z.boolean(),
  daily_briefing: z.boolean(),
  email_monitoring: z.boolean(),
});

type PersonalForm = z.infer<typeof personalSchema>;
type AcademicForm = z.infer<typeof academicSchema>;
type InstitutionForm = z.infer<typeof institutionSchema>;
type PreferencesForm = z.infer<typeof preferencesSchema>;

interface SubjectEntry {
  name: string;
  color: string;
}

const slideVariants = {
  enter: (dir: number) => ({ x: dir > 0 ? 300 : -300, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir: number) => ({ x: dir > 0 ? -300 : 300, opacity: 0 }),
};

export function OnboardingPage() {
  const navigate = useNavigate();
  const { user, refreshSession } = useAuthContext();
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [subjects, setSubjects] = useState<SubjectEntry[]>([]);
  const [newSubject, setNewSubject] = useState("");
  const [newSubjectColor, setNewSubjectColor] = useState(SUBJECT_COLORS[0]);
  const [editingSubjectIndex, setEditingSubjectIndex] = useState<number | null>(null);

  const defaultName = (user?.profile?.full_name || user?.user_metadata?.full_name || "") as string;

  const [formData, setFormData] = useState({
    personal: { full_name: defaultName, display_name: "" },
    academic: { education_type: "", education_year: "" },
    institution: { college_name: "", university_board: "", branch_stream: "", division: "", roll_number: "" },
    preferences: {
      theme: "dark" as "dark" | "light" | "system",
      daily_goal_hours: 2,
      pomodoro_focus: 25,
      pomodoro_break: 5,
      assignment_reminders: true,
      daily_briefing: true,
      email_monitoring: false,
    },
  });

  const personalForm = useForm<PersonalForm>({
    resolver: zodResolver(personalSchema),
    defaultValues: formData.personal,
  });

  const academicForm = useForm<AcademicForm>({
    resolver: zodResolver(academicSchema),
    defaultValues: formData.academic,
  });

  const institutionForm = useForm<InstitutionForm>({
    resolver: zodResolver(institutionSchema),
    defaultValues: formData.institution,
  });

  const preferencesForm = useForm<PreferencesForm>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: formData.preferences,
  });

  const educationType = academicForm.watch("education_type");
  const availableYears = educationType ? EDUCATION_YEARS[educationType] || [] : [];

  const goTo = (nextStep: number) => {
    setDirection(nextStep > step ? 1 : -1);
    setStep(nextStep);
  };

  const handlePersonalNext = personalForm.handleSubmit((data) => {
    setFormData((prev) => ({
      ...prev,
      personal: { full_name: data.full_name, display_name: data.display_name || "" },
    }));
    goTo(1);
  });

  const handleAcademicNext = academicForm.handleSubmit((data) => {
    setFormData((prev) => ({
      ...prev,
      academic: { education_type: data.education_type, education_year: data.education_year },
    }));
    goTo(2);
  });

  const handleInstitutionNext = institutionForm.handleSubmit((data) => {
    setFormData((prev) => ({
      ...prev,
      institution: {
        college_name: data.college_name,
        university_board: data.university_board,
        branch_stream: data.branch_stream,
        division: data.division || "",
        roll_number: data.roll_number || "",
      },
    }));
    goTo(3);
  });

  const handlePreferencesNext = preferencesForm.handleSubmit((data) => {
    setFormData((prev) => ({
      ...prev,
      preferences: {
        theme: data.theme,
        daily_goal_hours: data.daily_goal_hours,
        pomodoro_focus: data.pomodoro_focus,
        pomodoro_break: data.pomodoro_break,
        assignment_reminders: data.assignment_reminders,
        daily_briefing: data.daily_briefing,
        email_monitoring: data.email_monitoring,
      },
    }));
    goTo(4);
  });

  const addSubject = () => {
    const name = newSubject.trim();
    if (!name) return;
    if (editingSubjectIndex !== null) {
      setSubjects((prev) =>
        prev.map((s, i) => (i === editingSubjectIndex ? { ...s, name, color: newSubjectColor } : s)),
      );
      setEditingSubjectIndex(null);
    } else {
      setSubjects((prev) => [...prev, { name, color: newSubjectColor }]);
    }
    setNewSubject("");
    setNewSubjectColor(SUBJECT_COLORS[0]);
  };

  const editSubject = (index: number) => {
    setNewSubject(subjects[index].name);
    setNewSubjectColor(subjects[index].color);
    setEditingSubjectIndex(index);
  };

  const removeSubject = (index: number) => {
    setSubjects((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmitAll = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await completeOnboarding({
        profile: {
          full_name: formData.personal.full_name,
          display_name: formData.personal.display_name || null,
          education_type: formData.academic.education_type,
          education_year: formData.academic.education_year,
          college_name: formData.institution.college_name,
          university_board: formData.institution.university_board,
          branch_stream: formData.institution.branch_stream,
          division: formData.institution.division || null,
          roll_number: formData.institution.roll_number || null,
        },
        settings: formData.preferences,
        subjects: subjects.map((s) => ({ name: s.name, color: s.color })),
      });
      await refreshSession();
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Onboarding failed. Please try again.";
      setError(message);
      logger.error("Onboarding failed", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute left-1/3 top-1/4 h-72 w-72 -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />
          <div className="absolute bottom-1/4 right-1/3 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-2xl"
      >
        <div className="rounded-2xl border bg-card/80 p-8 shadow-2xl backdrop-blur-xl sm:p-10">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Welcome to Fixly
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Set up your academic profile to get started
            </p>
          </div>

          <div className="mb-8 flex items-center justify-center gap-2">
            {STEPS.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors ${
                    i <= step
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i + 1}
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className={`h-0.5 w-8 transition-colors ${
                      i < step ? "bg-primary" : "bg-muted"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              {step === 0 && (
                <form onSubmit={handlePersonalNext} className="space-y-5">
                  <h2 className="text-lg font-semibold">Personal Details</h2>
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input id="full_name" placeholder="John Doe" autoFocus {...personalForm.register("full_name")} />
                    {personalForm.formState.errors.full_name && (
                      <p className="text-xs text-destructive">{personalForm.formState.errors.full_name.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="display_name">Display Name <span className="text-muted-foreground">(optional)</span></Label>
                    <Input id="display_name" placeholder="How others see you" {...personalForm.register("display_name")} />
                  </div>
                  <div className="flex justify-end pt-4">
                    <Button type="submit">Next</Button>
                  </div>
                </form>
              )}

              {step === 1 && (
                <form onSubmit={handleAcademicNext} className="space-y-5">
                  <h2 className="text-lg font-semibold">Academic Information</h2>
                  <div className="space-y-2">
                    <Label htmlFor="education_type">Education Type</Label>
                    <select
                      id="education_type"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      {...academicForm.register("education_type")}
                    >
                      <option value="">Select education type</option>
                      {EDUCATION_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                    {academicForm.formState.errors.education_type && (
                      <p className="text-xs text-destructive">{academicForm.formState.errors.education_type.message}</p>
                    )}
                  </div>
                  {availableYears.length > 0 && (
                    <div className="space-y-2">
                      <Label htmlFor="education_year">Year</Label>
                      <select
                        id="education_year"
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        {...academicForm.register("education_year")}
                      >
                        <option value="">Select year</option>
                        {availableYears.map((y) => (
                          <option key={y} value={y}>{y}</option>
                        ))}
                      </select>
                      {academicForm.formState.errors.education_year && (
                        <p className="text-xs text-destructive">{academicForm.formState.errors.education_year.message}</p>
                      )}
                    </div>
                  )}
                  <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" onClick={() => goTo(0)}>Back</Button>
                    <Button type="submit">Next</Button>
                  </div>
                </form>
              )}

              {step === 2 && (
                <form onSubmit={handleInstitutionNext} className="space-y-5">
                  <h2 className="text-lg font-semibold">Institution Details</h2>
                  <div className="space-y-2">
                    <Label htmlFor="college_name">College Name</Label>
                    <Input id="college_name" placeholder="Your college or school" autoFocus {...institutionForm.register("college_name")} />
                    {institutionForm.formState.errors.college_name && (
                      <p className="text-xs text-destructive">{institutionForm.formState.errors.college_name.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="university_board">University / Board</Label>
                    <Input id="university_board" placeholder="e.g. Mumbai University, CBSE" {...institutionForm.register("university_board")} />
                    {institutionForm.formState.errors.university_board && (
                      <p className="text-xs text-destructive">{institutionForm.formState.errors.university_board.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="branch_stream">Branch / Stream</Label>
                    <Input id="branch_stream" placeholder="e.g. Computer Science, Science" {...institutionForm.register("branch_stream")} />
                    {institutionForm.formState.errors.branch_stream && (
                      <p className="text-xs text-destructive">{institutionForm.formState.errors.branch_stream.message}</p>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="division">Division <span className="text-muted-foreground">(optional)</span></Label>
                      <Input id="division" placeholder="A" {...institutionForm.register("division")} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="roll_number">Roll Number <span className="text-muted-foreground">(optional)</span></Label>
                      <Input id="roll_number" placeholder="12345" {...institutionForm.register("roll_number")} />
                    </div>
                  </div>
                  <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" onClick={() => goTo(1)}>Back</Button>
                    <Button type="submit">Next</Button>
                  </div>
                </form>
              )}

              {step === 3 && (
                <form onSubmit={handlePreferencesNext} className="space-y-5">
                  <h2 className="text-lg font-semibold">Preferences</h2>
                  <div className="space-y-2">
                    <Label>Theme</Label>
                    <div className="flex gap-3">
                      {(["dark", "light", "system"] as const).map((t) => (
                        <label key={t} className="flex cursor-pointer items-center gap-2 rounded-lg border p-3 has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                          <input type="radio" value={t} {...preferencesForm.register("theme")} className="accent-primary" />
                          <span className="text-sm capitalize">{t}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="daily_goal_hours">Daily Goal (hours)</Label>
                      <Input id="daily_goal_hours" type="number" min={0} max={24} {...preferencesForm.register("daily_goal_hours")} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="pomodoro_focus">Focus (min)</Label>
                      <Input id="pomodoro_focus" type="number" min={1} max={120} {...preferencesForm.register("pomodoro_focus")} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="pomodoro_break">Break (min)</Label>
                      <Input id="pomodoro_break" type="number" min={1} max={60} {...preferencesForm.register("pomodoro_break")} />
                    </div>
                  </div>
                  <div className="space-y-3 rounded-lg border p-4">
                    <h3 className="text-sm font-medium">Notifications</h3>
                    {[
                      { key: "assignment_reminders" as const, label: "Assignment reminders" },
                      { key: "daily_briefing" as const, label: "Daily briefing" },
                      { key: "email_monitoring" as const, label: "Email monitoring" },
                    ].map(({ key, label }) => (
                      <label key={key} className="flex cursor-pointer items-center gap-3">
                        <input type="checkbox" {...preferencesForm.register(key)} className="h-4 w-4 accent-primary" />
                        <span className="text-sm">{label}</span>
                      </label>
                    ))}
                  </div>
                  <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" onClick={() => goTo(2)}>Back</Button>
                    <Button type="submit">Next</Button>
                  </div>
                </form>
              )}

              {step === 4 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-semibold">Your Subjects</h2>
                  <p className="text-sm text-muted-foreground">
                    Add the subjects you&apos;re currently studying. You can always add more later.
                  </p>

                  <div className="flex gap-2">
                    <Input
                      placeholder="Subject name"
                      value={newSubject}
                      onChange={(e) => setNewSubject(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSubject())}
                      className="flex-1"
                    />
                    <div className="flex gap-1 rounded-md border p-1">
                      {SUBJECT_COLORS.slice(0, 8).map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setNewSubjectColor(c)}
                          className={`h-6 w-6 rounded-full transition-transform ${newSubjectColor === c ? "scale-125 ring-2 ring-ring ring-offset-1" : ""}`}
                          style={{ backgroundColor: c }}
                        />
                      ))}
                    </div>
                    <Button type="button" onClick={addSubject} variant="outline" size="sm">
                      {editingSubjectIndex !== null ? "Update" : "Add"}
                    </Button>
                  </div>

                  {subjects.length > 0 && (
                    <div className="space-y-2">
                      {subjects.map((s, i) => (
                        <div key={i} className="flex items-center gap-3 rounded-lg border px-4 py-3">
                          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: s.color }} />
                          <span className="flex-1 text-sm font-medium">{s.name}</span>
                          <button type="button" onClick={() => editSubject(i)} className="text-xs text-muted-foreground hover:text-foreground">Edit</button>
                          <button type="button" onClick={() => removeSubject(i)} className="text-xs text-destructive hover:text-destructive/80">Remove</button>
                        </div>
                      ))}
                    </div>
                  )}

                  {error && (
                    <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
                  )}

                  <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" onClick={() => goTo(3)}>Back</Button>
                    <Button onClick={handleSubmitAll} disabled={isSubmitting}>
                      {isSubmitting ? (
                        <span className="flex items-center gap-2">
                          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Setting up...
                        </span>
                      ) : (
                        "Complete Setup"
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
