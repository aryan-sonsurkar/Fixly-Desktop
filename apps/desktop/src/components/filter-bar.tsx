import { useState } from "react";
import { Button, Input } from "@fixly/ui";
import type { AssignmentsQuery } from "@/lib/assignment-service";
import type { Subject } from "@fixly/shared-types";

interface FilterBarProps {
  query: AssignmentsQuery;
  onChange: (query: AssignmentsQuery) => void;
  subjects: Subject[];
}

export function FilterBar({ query, onChange, subjects }: FilterBarProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [searchText, setSearchText] = useState(query.search || "");

  const update = (partial: Partial<AssignmentsQuery>) => {
    onChange({ ...query, ...partial, page: 1 });
  };

  const handleSearch = () => {
    update({ search: searchText || undefined });
  };

  const clearFilters = () => {
    setSearchText("");
    onChange({
      is_archived: false,
      sort_by: "created_at",
      sort_order: "desc",
      page: 1,
      page_size: 20,
    });
  };

  const hasActiveFilters = !!(
    query.search || query.status || query.priority || query.subject_id ||
    query.is_favorite || query.tags?.length
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <Input
            placeholder="Search assignments..."
            className="pl-9"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)}>
          Filters
          {hasActiveFilters && <span className="ml-1.5 h-2 w-2 rounded-full bg-primary" />}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => update({ sort_by: "created_at", sort_order: query.sort_order === "desc" ? "asc" : "desc" })}>
          Sort: {query.sort_by?.replace("_", " ")} ({query.sort_order})
        </Button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/30 p-4">
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={query.status || ""}
            onChange={(e) => update({ status: e.target.value || undefined })}
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={query.priority || ""}
            onChange={(e) => update({ priority: e.target.value || undefined })}
          >
            <option value="">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Critical</option>
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={query.subject_id || ""}
            onChange={(e) => update({ subject_id: e.target.value || undefined })}
          >
            <option value="">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>

          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={query.is_favorite || false}
              onChange={(e) => update({ is_favorite: e.target.checked || undefined })}
              className="h-4 w-4 accent-primary"
            />
            Favorites only
          </label>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear filters
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
