interface EmailWidgetProps {
  unread: number;
  pendingReview: number;
}

export function EmailWidget({ unread, pendingReview }: EmailWidgetProps) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
        </svg>
        <h3 className="text-sm font-semibold">Email</h3>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2">
          <span className="text-muted-foreground">Unread</span>
          <span className="font-semibold">{unread}</span>
        </div>
        <div className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2">
          <span className="text-muted-foreground">Pending Review</span>
          <span className="font-semibold">{pendingReview}</span>
        </div>
      </div>
    </div>
  );
}
