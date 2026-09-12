import { useState, useEffect, useCallback } from "react";
import {
  Button,
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@fixly/ui";
import {
  listGoals,
  createGoal,
  updateGoalProgress,
  listSkills,
  createSkill,
  listRoadmaps,
  createRoadmap,
  type Goal,
  type Skill,
  type Roadmap,
} from "@/lib/goals-service";

export function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"goals" | "skills" | "roadmap">("goals");

  const [goalTitle, setGoalTitle] = useState("");
  const [goalDesc, setGoalDesc] = useState("");
  const [goalCategory, setGoalCategory] = useState("academic");
  const [goalTargetDate, setGoalTargetDate] = useState("");

  const [skillName, setSkillName] = useState("");
  const [skillCategory, setSkillCategory] = useState("technical");

  const [roadmapTitle, setRoadmapTitle] = useState("");
  const [roadmapSteps, setRoadmapSteps] = useState("");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [g, s, r] = await Promise.all([
        listGoals(),
        listSkills(),
        listRoadmaps(),
      ]);
      setGoals(g);
      setSkills(s);
      setRoadmaps(r);
    } catch {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalTitle.trim()) return;
    setSaving(true);
    try {
      const g = await createGoal({
        title: goalTitle.trim(),
        description: goalDesc.trim(),
        category: goalCategory,
        target_date: goalTargetDate || undefined,
      });
      setGoals((prev) => [g, ...prev]);
      setGoalTitle("");
      setGoalDesc("");
      setGoalTargetDate("");
    } catch {
      setError("Failed to create goal");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillName.trim()) return;
    setSaving(true);
    try {
      const s = await createSkill({
        name: skillName.trim(),
        category: skillCategory,
      });
      setSkills((prev) => [s, ...prev]);
      setSkillName("");
    } catch {
      setError("Failed to create skill");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateRoadmap = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roadmapTitle.trim() || !roadmapSteps.trim()) return;
    setSaving(true);
    try {
      const steps = roadmapSteps
        .split("\n")
        .filter((s) => s.trim())
        .map((s) => ({ title: s.trim() }));
      const r = await createRoadmap({
        title: roadmapTitle.trim(),
        steps,
      });
      setRoadmaps((prev) => [r, ...prev]);
      setRoadmapTitle("");
      setRoadmapSteps("");
    } catch {
      setError("Failed to create roadmap");
    } finally {
      setSaving(false);
    }
  };

  const handleProgress = async (id: string, progress: number) => {
    try {
      const updated = await updateGoalProgress(id, progress);
      setGoals((prev) => prev.map((g) => (g.id === id ? updated : g)));
    } catch {
      setError("Failed to update progress");
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Goals & Roadmaps</h1>
        <p className="text-sm text-muted-foreground">
          Set goals, track skills, and plan learning roadmaps.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            dismiss
          </button>
        </div>
      )}

      <div className="flex gap-1 border-b">
        {(["goals", "skills", "roadmap"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t === "goals" ? "Goals" : t === "skills" ? "Skills" : "Roadmaps"}
          </button>
        ))}
      </div>

      {tab === "goals" && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">New Goal</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateGoal} className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs">Title</Label>
                  <Input
                    value={goalTitle}
                    onChange={(e) => setGoalTitle(e.target.value)}
                    placeholder="e.g. Master Calculus"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Description</Label>
                  <Input
                    value={goalDesc}
                    onChange={(e) => setGoalDesc(e.target.value)}
                    placeholder="Optional description"
                  />
                </div>
                <div className="flex gap-3">
                  <div className="flex-1 space-y-1">
                    <Label className="text-xs">Category</Label>
                    <select
                      value={goalCategory}
                      onChange={(e) => setGoalCategory(e.target.value)}
                      className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    >
                      <option value="academic">Academic</option>
                      <option value="career">Career</option>
                      <option value="personal">Personal</option>
                      <option value="health">Health</option>
                    </select>
                  </div>
                  <div className="flex-1 space-y-1">
                    <Label className="text-xs">Target Date</Label>
                    <Input
                      type="date"
                      value={goalTargetDate}
                      onChange={(e) => setGoalTargetDate(e.target.value)}
                    />
                  </div>
                </div>
                <Button type="submit" disabled={saving || !goalTitle.trim()}>
                  {saving ? "Creating..." : "Create Goal"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {goals.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No goals yet. Create your first goal above.
            </p>
          ) : (
            goals.map((goal) => (
              <Card key={goal.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="font-medium">{goal.title}</p>
                      {goal.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {goal.description}
                        </p>
                      )}
                      <div className="flex gap-2 mt-2">
                        <Badge variant="secondary" className="text-[10px]">
                          {goal.category}
                        </Badge>
                        {goal.target_date && (
                          <Badge variant="outline" className="text-[10px]">
                            Due {new Date(goal.target_date).toLocaleDateString()}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Progress</span>
                      <span>{goal.progress}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${goal.progress}%` }}
                      />
                    </div>
                    <div className="flex gap-1 mt-1">
                      {[0, 25, 50, 75, 100].map((p) => (
                        <Button
                          key={p}
                          size="sm"
                          variant={goal.progress === p ? "default" : "ghost"}
                          className="h-6 text-[10px] px-2"
                          onClick={() => handleProgress(goal.id, p)}
                        >
                          {p}%
                        </Button>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {tab === "skills" && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Add Skill</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateSkill} className="flex gap-3 items-end">
                <div className="flex-1 space-y-1">
                  <Label className="text-xs">Skill Name</Label>
                  <Input
                    value={skillName}
                    onChange={(e) => setSkillName(e.target.value)}
                    placeholder="e.g. Python"
                  />
                </div>
                <div className="w-36 space-y-1">
                  <Label className="text-xs">Category</Label>
                  <select
                    value={skillCategory}
                    onChange={(e) => setSkillCategory(e.target.value)}
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  >
                    <option value="technical">Technical</option>
                    <option value="academic">Academic</option>
                    <option value="soft">Soft Skill</option>
                    <option value="language">Language</option>
                  </select>
                </div>
                <Button type="submit" disabled={saving || !skillName.trim()}>
                  Add
                </Button>
              </form>
            </CardContent>
          </Card>

          {skills.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No skills tracked yet.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {skills.map((skill) => (
                <Card key={skill.id}>
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm">{skill.name}</p>
                      <Badge variant="secondary" className="text-[10px]">
                        {skill.level}
                      </Badge>
                    </div>
                    <Badge variant="outline" className="text-[10px] mt-1">
                      {skill.category}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "roadmap" && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Create Roadmap
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateRoadmap} className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs">Title</Label>
                  <Input
                    value={roadmapTitle}
                    onChange={(e) => setRoadmapTitle(e.target.value)}
                    placeholder="e.g. Learn Machine Learning"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Steps (one per line)</Label>
                  <textarea
                    value={roadmapSteps}
                    onChange={(e) => setRoadmapSteps(e.target.value)}
                    rows={4}
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    placeholder={"1. Learn Python basics\n2. Study linear algebra\n3. Build first model"}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={saving || !roadmapTitle.trim() || !roadmapSteps.trim()}
                >
                  {saving ? "Creating..." : "Create Roadmap"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {roadmaps.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No roadmaps yet.
            </p>
          ) : (
            roadmaps.map((roadmap) => (
              <Card key={roadmap.id}>
                <CardContent className="p-4">
                  <p className="font-medium">{roadmap.title}</p>
                  <div className="mt-2 space-y-1">
                    {roadmap.steps
                      .sort((a, b) => a.order - b.order)
                      .map((step) => (
                        <div
                          key={step.id}
                          className="flex items-center gap-2 text-sm"
                        >
                          <span
                            className={
                              step.status === "completed"
                                ? "text-green-500"
                                : "text-muted-foreground"
                            }
                          >
                            {step.status === "completed" ? "✓" : "○"}
                          </span>
                          <span
                            className={
                              step.status === "completed"
                                ? "line-through text-muted-foreground"
                                : ""
                            }
                          >
                            {step.title}
                          </span>
                          {step.estimated_hours > 0 && (
                            <span className="text-[10px] text-muted-foreground ml-auto">
                              ~{step.estimated_hours}h
                            </span>
                          )}
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
