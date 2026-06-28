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
  type EmailMessage,
} from "@/lib/email-service";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

const categoryColors: Record<string, string> = {
  assignment: "bg-blue-500/10 text-blue-500",
  exam: "bg-red-500/10 text-red-500",
  project: "bg-purple-500/10 text-purple-500",
  notice: "bg-yellow-500/10 text-yellow-500",
  holiday: "bg-green-500/10 text-green-500",
  event: "bg-orange-500/10 text-orange-500",
  general: "bg-gray-500/10 text-gray-500",
  spam: "bg-red-500/10 text-red-500",
};

export function EmailPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"inbox" | "queue" | "accounts">("inbox");
  const [search, setSearch] = useState("");
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [briefingContent, setBriefingContent] = useState<string | null>(null);

  const { data: accounts } = useQuery({
    queryKey: ["email-accounts"],
    queryFn: getEmailAccounts,
  });

  const { data: inbox, isLoading: inboxLoading } = useQuery({
    queryKey: ["email-messages", search],
    queryFn: () => getEmailMessages({ search: search || undefined, page_size: 50 }),
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
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteEmailAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-accounts"] }),
  });

  const briefingMutation = useMutation({
    mutationFn: generateBriefing,
    onSuccess: (data) => setBriefingContent(data.content),
  });

  const handleMarkRead = async (msg: EmailMessage) => {
    if (!msg.is_read) {
      await markEmailRead(msg.id);
      queryClient.invalidateQueries({ queryKey: ["email-messages"] });
    }
    setSelectedEmail(msg);
  };

  const messages = inbox?.messages || [];
  const queueItems = queue || [];

  return (
    <div className="mx-auto flex max-w-7xl gap-4 p-4 h-full">
      {/* Left Panel */}
      <div className="flex w-64 shrink-0 flex-col gap-2">
        <h1 className="text-lg font-bold">Email</h1>
        <div className="flex flex-col gap-1">
          <Button variant={activeTab === "inbox" ? "default" : "ghost"} size="sm" className="justify-start" onClick={() => setActiveTab("inbox")}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            Inbox
            {inbox && messages.filter(m => !m.is_read).length > 0 && (
              <Badge variant="default" className="ml-auto text-xs">{messages.filter(m => !m.is_read).length}</Badge>
            )}
          </Button>
          <Button variant={activeTab === "queue" ? "default" : "ghost"} size="sm" className="justify-start" onClick={() => setActiveTab("queue")}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Review Queue
            {queueItems.length > 0 && (
              <Badge variant="secondary" className="ml-auto text-xs">{queueItems.length}</Badge>
            )}
          </Button>
          <Button variant={activeTab === "accounts" ? "default" : "ghost"} size="sm" className="justify-start" onClick={() => setActiveTab("accounts")}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Accounts
          </Button>
        </div>
        <div className="mt-auto">
          <Button variant="outline" size="sm" className="w-full" onClick={() => briefingMutation.mutate()} disabled={briefingMutation.isPending}>
            {briefingMutation.isPending ? "Generating..." : "Daily Briefing"}
          </Button>
        </div>
      </div>

      {/* Center / Right Panel */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeTab === "inbox" && (
          <div className="flex h-full flex-col">
            <div className="mb-3">
              <Input
                placeholder="Search emails..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-sm"
              />
            </div>
            {selectedEmail ? (
              <div className="flex-1 overflow-y-auto">
                <Button variant="ghost" size="sm" onClick={() => setSelectedEmail(null)} className="mb-3">
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
            ) : inboxLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 rounded-lg" />
                ))}
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
                    onClick={() => handleMarkRead(msg)}
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
        )}

        {activeTab === "queue" && (
          <div className="h-full overflow-y-auto">
            <h2 className="mb-3 text-base font-semibold">Review Queue</h2>
            {queueItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pending reviews.</p>
            ) : (
              <div className="space-y-2">
                {queueItems.map((item) => (
                  <Card key={item.id}>
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{item.title || "Untitled"}</p>
                          <p className="text-xs text-muted-foreground">
                            {item.subject && `${item.subject} · `}
                            Confidence: {Math.round(item.confidence * 100)}% · Status: {item.status}
                          </p>
                          {item.due_date && (
                            <p className="mt-1 text-xs text-muted-foreground">Due: {new Date(item.due_date).toLocaleDateString()}</p>
                          )}
                        </div>
                        <Badge variant={item.confidence >= 0.95 ? "default" : "secondary"}>
                          {item.confidence >= 0.95 ? "High" : item.confidence >= 0.70 ? "Medium" : "Low"}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "accounts" && (
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
                        <Button size="sm" variant="outline" onClick={() => syncMutation.mutate(acct.id)} disabled={syncMutation.isPending}>
                          Sync
                        </Button>
                        <Button size="sm" variant="destructive" onClick={() => deleteMutation.mutate(acct.id)}>
                          Disconnect
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
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
