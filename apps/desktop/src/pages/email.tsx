import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDebouncedValue } from "@/hooks/use-debounce";
import { motion } from "framer-motion";
import { Button, Input, Badge, Skeleton, Card, CardContent } from "@fixly/ui";
import {
  getEmailAccounts,
  getEmailMessages,
  syncEmailAccount,
  deleteEmailAccount,
  markEmailRead,
  connectEmailAccount,
  type EmailMessage,
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

export function EmailPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"inbox" | "accounts">("inbox");
  const [search, setSearch] = useState("");
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const debouncedSearch = useDebouncedValue(search, 300);

  const { data: accounts } = useQuery({
    queryKey: ["email-accounts"],
    queryFn: getEmailAccounts,
    staleTime: 60 * 1000,
    placeholderData: (prev) => prev,
  });

  const { data: inbox, isLoading: inboxLoading } = useQuery({
    queryKey: ["email-messages", debouncedSearch],
    queryFn: () => getEmailMessages({
      search: debouncedSearch || undefined,
      page_size: 50,
    }),
    staleTime: 30 * 1000,
    placeholderData: (prev) => prev,
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => syncEmailAccount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["email-messages"] });
      toast({ type: "success", title: "Email synced" });
    },
    onError: () => toast({ type: "error", title: "Failed to sync email" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteEmailAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-accounts"] }),
  });

  const handleMarkRead = async (msg: EmailMessage) => {
    if (!msg.is_read) {
      try {
        await markEmailRead(msg.id);
        queryClient.invalidateQueries({ queryKey: ["email-messages"] });
      } catch {
        // silent
      }
    }
    setSelectedEmail(msg);
  };

  const messages = inbox?.messages || [];
  const unreadCount = messages.filter((m) => !m.is_read).length;

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">Email</h1>

      <div className="flex gap-1 rounded-lg border bg-muted/50 p-1">
        <button
          type="button"
          onClick={() => setActiveTab("inbox")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${activeTab === "inbox" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
        >
          Inbox
          {unreadCount > 0 && <Badge variant="default" className="ml-2 text-xs">{unreadCount}</Badge>}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("accounts")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${activeTab === "accounts" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
        >
          Accounts
        </button>
      </div>

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

      {activeTab === "accounts" && (
        <AccountsView
          accounts={accounts || []}
          onSync={(id) => syncMutation.mutate(id)}
          onDelete={(id) => deleteMutation.mutate(id)}
        />
      )}
    </div>
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
    <div className="flex flex-col">
      <Input placeholder="Search emails..." value={search} onChange={(e) => onSearchChange(e.target.value)} className="max-w-sm" />

      {selectedEmail ? (
        <div className="mt-4">
          <Button variant="ghost" size="sm" onClick={onBack} className="mb-3">
            ← Back
          </Button>
          <Card>
            <CardContent className="pt-6">
              <h2 className="text-lg font-semibold">{selectedEmail.subject}</h2>
              <p className="text-sm text-muted-foreground">
                {selectedEmail.from_name || selectedEmail.from_email} · {formatDate(selectedEmail.received_at)}
              </p>
              {selectedEmail.classification && (
                <Badge variant="outline" className={`mt-2 ${categoryColors[selectedEmail.classification.category] || ""}`}>
                  {selectedEmail.classification.category}
                </Badge>
              )}
              <div className="mt-4 whitespace-pre-wrap text-sm">
                {selectedEmail.body_text || "No text content"}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : loading ? (
        <div className="mt-4 space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)}
        </div>
      ) : messages.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-sm text-muted-foreground">No emails yet. Connect an account to get started.</p>
        </div>
      ) : (
        <div className="mt-4 space-y-1">
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

function AccountsView({ accounts, onSync, onDelete }: { accounts: any[]; onSync: (id: string) => void; onDelete: (id: string) => void }) {
  const [email, setEmail] = useState("");
  const [appPassword, setAppPassword] = useState("");
  const queryClient = useQueryClient();
  const connectMut = useMutation({
    mutationFn: () => {
      const isGmail = email.toLowerCase().endsWith("@gmail.com");
      return connectEmailAccount({ email, provider: isGmail ? "gmail" : "other", access_token: appPassword });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-accounts"] });
      setEmail(""); setAppPassword("");
      toast({ type: "success", title: "Account connected" });
    },
    onError: () => toast({ type: "error", title: "Failed to connect — check App Password" }),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="pt-4">
          <h3 className="text-sm font-semibold">Connect Gmail</h3>
          <p className="text-xs text-muted-foreground mb-3">
            Create an App Password at myaccount.google.com → Security → App Passwords.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input placeholder="you@gmail.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Input placeholder="16-char App Password" type="password" value={appPassword} onChange={(e) => setAppPassword(e.target.value)} />
          </div>
          <Button size="sm" className="mt-3" onClick={() => connectMut.mutate()} disabled={!email || !appPassword || connectMut.isPending}>
            {connectMut.isPending ? "Connecting..." : "Connect"}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-base font-semibold">Connected Accounts</h2>
        {!accounts || accounts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No accounts connected yet.</p>
        ) : (
          <div className="space-y-3">
            {accounts.map((acct) => (
              <Card key={acct.id}>
                <CardContent className="flex items-center justify-between pt-4">
                  <div>
                    <p className="font-medium">{acct.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {acct.total_emails} emails
                      {acct.last_synced_at ? ` · Last sync: ${formatDate(acct.last_synced_at)}` : ""}
                    </p>
                    <span className={`mt-1 inline-block h-2 w-2 rounded-full ${acct.sync_status === "error" ? "bg-red-500" : "bg-green-500"}`} />
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
    </div>
  );
}
