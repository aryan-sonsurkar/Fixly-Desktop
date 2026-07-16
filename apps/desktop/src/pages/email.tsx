import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Button, Input, Badge, Skeleton, Card, CardContent, CardHeader, CardTitle } from "@fixly/ui";
import {
  getEmailAccounts,
  getEmailMessages,
  getReviewQueue,
  syncEmailAccount,
  deleteEmailAccount,
  markEmailRead,
  generateBriefing,
  reviewAssignment,
  type EmailMessage,
  type EmailAssignment,
} from "@/lib/email-service";
import { toast } from "@/stores/toast-store";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

const categoryColors: Record<string, string> = {
  assignment: "bg-blue-500/10 text-blue-500",
  exam: "bg-red-500/10 text-red-500",
  internship: "bg-green-500/10 text-green-500",
  placement: "bg-purple-500/10 text-purple-500",
  scholarship: "bg-yellow-500/10 text-yellow-500",
  circular: "bg-orange-500/10 text-orange-500",
  project: "bg-indigo-500/10 text-indigo-500",
  holiday: "bg-emerald-500/10 text-emerald-500",
  event: "bg-pink-500/10 text-pink-500",
  general: "bg-gray-500/10 text-gray-500",
  spam: "bg-red-500/10 text-red-500",
};

const categoryIcons: Record<string, string> = {
  assignment: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  exam: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
  internship: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
  placement: "M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z",
  scholarship: "M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  circular: "M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3l-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 003.7 3.7 48.656 48.656 0 007.324 0 4.006 4.006 0 003.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3l-3 3",
};

const smartCategories = [
  { key: "assignment", label: "Assignments", icon: categoryIcons.assignment },
  { key: "exam", label: "Exams", icon: categoryIcons.exam },
  { key: "internship", label: "Internships", icon: categoryIcons.internship },
  { key: "placement", label: "Placements", icon: categoryIcons.placement },
  { key: "scholarship", label: "Scholarships", icon: categoryIcons.scholarship },
  { key: "circular", label: "Circulars", icon: categoryIcons.circular },
];

export function EmailPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"inbox" | "queue" | "accounts" | "categories">("inbox");
  const [search, setSearch] = useState("");
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [briefingContent, setBriefingContent] = useState<string | null>(null);

  const { data: accounts } = useQuery({
    queryKey: ["email-accounts"],
    queryFn: getEmailAccounts,
  });

  const { data: inbox, isLoading: inboxLoading } = useQuery({
    queryKey: ["email-messages", search],
    queryFn: () => getEmailMessages({
      search: search || undefined,
      page_size: 50,
    }),
  });

  const { data: queue } = useQuery({
    queryKey: ["email-review-queue"],
    queryFn: getReviewQueue,
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => syncEmailAccount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["email-messages"] });
      toast({ type: "success", title: "Email synced successfully" });
    },
    onError: () => toast({ type: "error", title: "Failed to sync email" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteEmailAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-accounts"] }),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => reviewAssignment(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-review-queue"] });
      toast({ type: "success", title: "Review decision saved" });
    },
    onError: () => toast({ type: "error", title: "Failed to process review" }),
  });

  const briefingMutation = useMutation({
    mutationFn: generateBriefing,
    onSuccess: (data) => {
      setBriefingContent(data.content);
      toast({ type: "success", title: "Briefing generated" });
    },
    onError: () => toast({ type: "error", title: "Failed to generate briefing" }),
  });

  const handleMarkRead = async (msg: EmailMessage) => {
    if (!msg.is_read) {
      try {
        await markEmailRead(msg.id);
        queryClient.invalidateQueries({ queryKey: ["email-messages"] });
      } catch {
        toast({ type: "error", title: "Failed to mark email as read" });
      }
    }
    setSelectedEmail(msg);
  };

  const messages = inbox?.messages || [];
  const queueItems = queue || [];

  return (
    <div className="mx-auto flex max-w-7xl gap-4 p-4 h-full">
      <div className="flex w-64 shrink-0 flex-col gap-2">
        <h1 className="text-lg font-bold">Email Intelligence</h1>
        <div className="flex flex-col gap-1">
          <NavButton active={activeTab === "inbox"} onClick={() => setActiveTab("inbox")} icon="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" label="Inbox" badge={messages.filter(m => !m.is_read).length} />
          <NavButton active={activeTab === "categories"} onClick={() => setActiveTab("categories")} icon="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" label="Smart Categories" />
          <NavButton active={activeTab === "queue"} onClick={() => setActiveTab("queue")} icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" label="Review Queue" badge={queueItems.length} />
          <NavButton active={activeTab === "accounts"} onClick={() => setActiveTab("accounts")} icon="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" label="Accounts" />
        </div>
        <div className="mt-auto space-y-2">
          <Button variant="outline" size="sm" className="w-full" onClick={() => briefingMutation.mutate()} disabled={briefingMutation.isPending}>
            {briefingMutation.isPending ? "Generating..." : "Daily Briefing"}
          </Button>
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        {activeTab === "inbox" && (
          <InboxView
            messages={messages}
            loading={inboxLoading}
            search={search}
            onSearchChange={setSearch}
            selectedEmail={selectedEmail}
            onSelectEmail={handleMarkRead}
            onBack={() => setSelectedEmail(null)}
          />
        )}

        {activeTab === "categories" && (
          <CategoriesView messages={messages} />
        )}

        {activeTab === "queue" && (
          <div className="h-full overflow-y-auto">
            <h2 className="mb-3 text-base font-semibold">Review Queue</h2>
            <p className="mb-4 text-xs text-muted-foreground">
              Items detected from emails that need your review before becoming assignments
            </p>
            {queueItems.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-16 text-center">
                <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-muted-foreground">No pending reviews</p>
              </div>
            ) : (
              <div className="space-y-2">
                {queueItems.map((item: EmailAssignment) => (
                  <motion.div key={item.id} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{item.title || "Untitled"}</p>
                              <Badge variant={item.confidence >= 0.95 ? "default" : "secondary"} className="text-[10px]">
                                {Math.round(item.confidence * 100)}%
                              </Badge>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {item.subject && `${item.subject} · `}
                              {item.teacher_name && `From: ${item.teacher_name} · `}
                              Status: {item.status}
                            </p>
                            {item.due_date && (
                              <p className="mt-1 text-xs text-muted-foreground">
                                Due: {new Date(item.due_date).toLocaleDateString()}
                              </p>
                            )}
                            {item.description && (
                              <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{item.description}</p>
                            )}
                          </div>
                        </div>
                        <div className="mt-3 flex gap-2">
                          <Button size="sm" onClick={() => reviewMutation.mutate({ id: item.id, status: "approved" })} disabled={reviewMutation.isPending}>
                            Approve
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => reviewMutation.mutate({ id: item.id, status: "rejected" })} disabled={reviewMutation.isPending}>
                            Reject
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "accounts" && (
          <AccountsView accounts={accounts || []} onSync={(id) => syncMutation.mutate(id)} onDelete={(id) => deleteMutation.mutate(id)} />
        )}

        {briefingContent && (
          <Card className="mt-4">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Daily Briefing</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setBriefingContent(null)}>Close</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm">
                {briefingContent}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function NavButton({ active, onClick, icon, label, badge }: { active: boolean; onClick: () => void; icon: string; label: string; badge?: number }) {
  return (
    <Button variant={active ? "default" : "ghost"} size="sm" className="justify-start" onClick={onClick}>
      <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
      </svg>
      {label}
      {badge !== undefined && badge > 0 && (
        <Badge variant="default" className="ml-auto text-xs">{badge}</Badge>
      )}
    </Button>
  );
}

function InboxView({
  messages, loading, search, onSearchChange, selectedEmail, onSelectEmail, onBack,
}: {
  messages: EmailMessage[];
  loading: boolean;
  search: string;
  onSearchChange: (s: string) => void;
  selectedEmail: EmailMessage | null;
  onSelectEmail: (msg: EmailMessage) => void;
  onBack: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-3">
        <Input placeholder="Search emails..." value={search} onChange={(e) => onSearchChange(e.target.value)} className="max-w-sm" />
      </div>
      {selectedEmail ? (
        <div className="flex-1 overflow-y-auto">
          <Button variant="ghost" size="sm" onClick={onBack} className="mb-3">
            <svg className="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
            Back
          </Button>
          <Card>
            <CardContent className="pt-6">
              <h2 className="text-lg font-semibold">{selectedEmail.subject}</h2>
              <p className="text-sm text-muted-foreground">
                {selectedEmail.from_name || selectedEmail.from_email} &middot; {formatDate(selectedEmail.received_at)}
              </p>
              {selectedEmail.classification && (
                <Badge variant="outline" className={`mt-2 ${categoryColors[selectedEmail.classification.category] || ""}`}>
                  {selectedEmail.classification.category} ({Math.round(selectedEmail.classification.confidence * 100)}%)
                </Badge>
              )}
              <div className="mt-4 whitespace-pre-wrap text-sm">
                {selectedEmail.body_text || "No text content"}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}
        </div>
      ) : messages.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-sm text-muted-foreground">No emails yet. Connect an account to get started.</p>
        </div>
      ) : (
        <div className="flex-1 space-y-1 overflow-y-auto">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={() => onSelectEmail(msg)}
              className={`flex cursor-pointer items-start gap-3 rounded-lg p-3 text-sm transition-colors hover:bg-accent ${!msg.is_read ? "border-l-2 border-l-primary bg-card" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  {!msg.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />}
                  <p className={`truncate ${!msg.is_read ? "font-medium" : ""}`}>{msg.subject || "(No subject)"}</p>
                </div>
                <p className="truncate text-xs text-muted-foreground">{msg.from_name || msg.from_email}</p>
                <div className="mt-1 flex items-center gap-2">
                  {msg.classification && (
                    <Badge variant="outline" className={`text-[10px] px-1 py-0 ${categoryColors[msg.classification.category] || ""}`}>
                      {msg.classification.category}
                    </Badge>
                  )}
                  <span className="text-[10px] text-muted-foreground">{formatDate(msg.received_at)}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

function CategoriesView({ messages }: { messages: EmailMessage[] }) {
  const grouped = messages.reduce<Record<string, EmailMessage[]>>((acc, m) => {
    const cat = m.classification?.category || "general";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(m);
    return acc;
  }, {});

  return (
    <div className="h-full overflow-y-auto">
      <h2 className="mb-1 text-base font-semibold">Smart Categories</h2>
      <p className="mb-4 text-xs text-muted-foreground">AI-classified emails organized by type</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {smartCategories.map((cat) => {
          const catMessages = grouped[cat.key] || [];
          return (
            <Card key={cat.key} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <svg className={`h-5 w-5 ${categoryColors[cat.key] || "text-muted-foreground"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={cat.icon} />
                  </svg>
                  <CardTitle className="text-sm">{cat.label}</CardTitle>
                  <Badge variant="outline" className="ml-auto text-xs">{catMessages.length}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                {catMessages.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No emails in this category</p>
                ) : (
                  <div className="space-y-1">
                    {catMessages.slice(0, 3).map((m) => (
                      <div key={m.id} className="rounded-lg bg-muted/30 px-2.5 py-1.5 text-xs">
                        <p className="truncate font-medium">{m.subject || "(No subject)"}</p>
                        <p className="text-muted-foreground">{m.from_name || m.from_email}</p>
                      </div>
                    ))}
                    {catMessages.length > 3 && (
                      <p className="text-xs text-muted-foreground">+{catMessages.length - 3} more</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      {messages.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="text-sm text-muted-foreground">Connect an account to see smart categories</p>
        </div>
      )}
    </div>
  );
}

function AccountsView({ accounts, onSync, onDelete }: { accounts: any[]; onSync: (id: string) => void; onDelete: (id: string) => void }) {
  return (
    <div className="h-full overflow-y-auto">
      <h2 className="mb-3 text-base font-semibold">Connected Accounts</h2>
      {!accounts || accounts.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <svg className="h-12 w-12 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="text-sm text-muted-foreground">No email accounts connected</p>
          <p className="text-xs text-muted-foreground">Connect a Gmail account to enable email intelligence</p>
        </div>
      ) : (
        <div className="space-y-3">
          {accounts.map((acct) => (
            <Card key={acct.id}>
              <CardContent className="flex items-center justify-between pt-4">
                <div>
                  <p className="font-medium">{acct.email}</p>
                  <p className="text-xs text-muted-foreground">
                    {acct.provider} · {acct.total_emails} emails
                    {acct.last_synced_at ? ` · Last sync: ${formatDate(acct.last_synced_at)}` : ""}
                  </p>
                  <Badge variant="outline" className={`mt-1 text-xs ${acct.sync_status === "syncing" ? "text-blue-500" : acct.sync_status === "error" ? "text-red-500" : "text-green-500"}`}>
                    {acct.sync_status}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => onSync(acct.id)}>Sync</Button>
                  <Button size="sm" variant="destructive" onClick={() => onDelete(acct.id)}>Disconnect</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
