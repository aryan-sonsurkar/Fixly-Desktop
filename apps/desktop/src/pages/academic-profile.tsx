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
  getAcademicProfile,
  updateScore,
  getRecommendations,
  type AcademicProfile,
} from "@/lib/academic-service";

export function AcademicProfilePage() {
  const [profile, setProfile] = useState<AcademicProfile | null>(null);
  const [recommendations, setRecommendations] = useState<
    Array<{
      subject: string;
      reason: string;
      priority: string;
      suggested_action: string;
    }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [subjectInput, setSubjectInput] = useState("");
  const [scoreInput, setScoreInput] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, r] = await Promise.all([
        getAcademicProfile(),
        getRecommendations(),
      ]);
      setProfile(p);
      setRecommendations(r);
    } catch {
      setError("Failed to load academic profile");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleAddScore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectInput.trim() || !scoreInput) return;
    setSaving(true);
    try {
      const updated = await updateScore({
        subject: subjectInput.trim(),
        score: Number(scoreInput),
      });
      setProfile(updated);
      setSubjectInput("");
      setScoreInput("");
    } catch {
      setError("Failed to save score");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-muted animate-pulse rounded" />
          <div className="h-4 w-64 bg-muted animate-pulse rounded" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  const subjects = profile?.subjects || {};
  const subjectList = Object.entries(subjects);
  const strengths = profile?.strengths || [];
  const weaknesses = profile?.weaknesses || [];

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Academic Profile</h1>
        <p className="text-sm text-muted-foreground">
          Track your academic performance and get personalized recommendations.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 underline hover:no-underline"
          >
            dismiss
          </button>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Add Score</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddScore} className="flex gap-3 items-end">
            <div className="flex-1 space-y-1">
              <Label htmlFor="subject" className="text-xs">
                Subject
              </Label>
              <Input
                id="subject"
                value={subjectInput}
                onChange={(e) => setSubjectInput(e.target.value)}
                placeholder="e.g. Mathematics"
              />
            </div>
            <div className="w-24 space-y-1">
              <Label htmlFor="score" className="text-xs">
                Score (0-100)
              </Label>
              <Input
                id="score"
                type="number"
                min={0}
                max={100}
                value={scoreInput}
                onChange={(e) => setScoreInput(e.target.value)}
                placeholder="85"
              />
            </div>
            <Button type="submit" disabled={saving || !subjectInput.trim() || !scoreInput}>
              {saving ? "Saving..." : "Add"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {subjectList.map(([name, data]) => (
          <Card key={name}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">{name}</CardTitle>
                <Badge
                  variant={
                    data.trend === "up"
                      ? "default"
                      : data.trend === "down"
                        ? "destructive"
                        : "secondary"
                  }
                  className="text-[10px]"
                >
                  {data.trend === "up" ? "↑ Improving" : data.trend === "down" ? "↓ Declining" : "→ Stable"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">
                  {Math.round(data.average_score)}
                </span>
                <span className="text-xs text-muted-foreground">
                  average ({data.scores.length} score{data.scores.length !== 1 ? "s" : ""})
                </span>
              </div>
              <div className="flex gap-2 text-xs text-muted-foreground">
                <span>{data.total_study_hours}h studied</span>
              </div>
              {data.weak_topics.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-[10px] text-muted-foreground">Weak:</span>
                  {data.weak_topics.map((t) => (
                    <Badge key={t} variant="destructive" className="text-[10px]">
                      {t}
                    </Badge>
                  ))}
                </div>
              )}
              {data.strong_topics.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-[10px] text-muted-foreground">Strong:</span>
                  {data.strong_topics.map((t) => (
                    <Badge key={t} variant="default" className="text-[10px]">
                      {t}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {(strengths.length > 0 || weaknesses.length > 0) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Strengths & Weaknesses
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {strengths.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Strengths</p>
                <div className="flex flex-wrap gap-1">
                  {strengths.map((s) => (
                    <Badge key={s} variant="default" className="text-xs">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {weaknesses.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Weaknesses</p>
                <div className="flex flex-wrap gap-1">
                  {weaknesses.map((w) => (
                    <Badge key={w} variant="destructive" className="text-xs">
                      {w}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {recommendations.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {recommendations.map((rec, i) => (
              <div key={i} className="border-l-2 border-primary pl-3 py-1">
                <p className="text-sm font-medium">{rec.subject}</p>
                <p className="text-xs text-muted-foreground">{rec.reason}</p>
                <p className="text-xs text-muted-foreground italic mt-0.5">
                  {rec.suggested_action}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {subjectList.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No academic data yet. Add your first score above to get started.
          </p>
        </div>
      )}
    </div>
  );
}
