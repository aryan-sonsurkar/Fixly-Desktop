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
  listOpportunities,
  saveOpportunity,
  updateOpportunityStatus,
  deleteOpportunity,
  type Opportunity,
} from "@/lib/opportunity-service";

export function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [category, setCategory] = useState("internship");
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listOpportunities(statusFilter || undefined);
      setOpportunities(data);
    } catch {
      setError("Failed to load opportunities");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !company.trim()) return;
    setSaving(true);
    try {
      const opp = await saveOpportunity({
        title: title.trim(),
        company: company.trim(),
        category,
        url: url.trim() || undefined,
        description: description.trim() || undefined,
        deadline: deadline || undefined,
      });
      setOpportunities((prev) => [opp, ...prev]);
      setTitle("");
      setCompany("");
      setUrl("");
      setDescription("");
      setDeadline("");
    } catch {
      setError("Failed to save opportunity");
    } finally {
      setSaving(false);
    }
  };

  const handleStatus = async (id: string, status: string) => {
    try {
      const updated = await updateOpportunityStatus(id, status);
      setOpportunities((prev) => prev.map((o) => (o.id === id ? updated : o)));
    } catch {
      setError("Failed to update status");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteOpportunity(id);
      setOpportunities((prev) => prev.filter((o) => o.id !== id));
    } catch {
      setError("Failed to delete");
    }
  };

  const STATUS_COLORS: Record<string, string> = {
    saved: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    applied:
      "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
    interview:
      "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    rejected:
      "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    accepted:
      "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-40 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Opportunities</h1>
        <p className="text-sm text-muted-foreground">
          Track internships, jobs, competitions, and other opportunities.
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

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Add Opportunity</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Title</Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Software Engineering Intern"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Company</Label>
                <Input
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Google"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Category</Label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                >
                  <option value="internship">Internship</option>
                  <option value="job">Job</option>
                  <option value="competition">Competition</option>
                  <option value="scholarship">Scholarship</option>
                  <option value="hackathon">Hackathon</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Deadline</Label>
                <Input
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">URL</Label>
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://..."
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Description</Label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="Brief description..."
              />
            </div>
            <Button type="submit" disabled={saving || !title.trim() || !company.trim()}>
              {saving ? "Saving..." : "Save Opportunity"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        {["", "saved", "applied", "interview", "accepted", "rejected"].map(
          (s) => (
            <Button
              key={s}
              size="sm"
              variant={statusFilter === s ? "default" : "outline"}
              onClick={() => setStatusFilter(s)}
            >
              {s || "All"}
            </Button>
          )
        )}
      </div>

      {opportunities.length === 0 ? (
        <p className="text-center text-muted-foreground py-8">
          No opportunities yet.
        </p>
      ) : (
        <div className="space-y-3">
          {opportunities.map((opp) => (
            <Card key={opp.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{opp.title}</p>
                      <Badge
                        className={`text-[10px] ${STATUS_COLORS[opp.status] || ""}`}
                      >
                        {opp.status}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {opp.category}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {opp.company}
                    </p>
                    {opp.description && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {opp.description}
                      </p>
                    )}
                    <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                      {opp.deadline && (
                        <span>
                          Deadline:{" "}
                          {new Date(opp.deadline).toLocaleDateString()}
                        </span>
                      )}
                      {opp.url && (
                        <a
                          href={opp.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          Link →
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    {["saved", "applied", "interview", "accepted", "rejected"]
                      .filter((s) => s !== opp.status)
                      .slice(0, 2)
                      .map((s) => (
                        <Button
                          key={s}
                          size="sm"
                          variant="ghost"
                          className="h-7 text-[10px] px-2"
                          onClick={() => handleStatus(opp.id, s)}
                        >
                          {s}
                        </Button>
                      ))}
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-[10px] px-2 text-destructive"
                      onClick={() => handleDelete(opp.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
