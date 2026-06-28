export function AssignmentSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-8 w-48 animate-pulse rounded-lg bg-muted" />
          <div className="h-4 w-72 animate-pulse rounded-lg bg-muted" />
        </div>
        <div className="h-10 w-36 animate-pulse rounded-lg bg-muted" />
      </div>

      <div className="h-10 animate-pulse rounded-lg bg-muted" />

      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" style={{ animationDelay: `${i * 100}ms` }} />
      ))}
    </div>
  );
}
