import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAIStore } from "@/stores/ai-store";
import * as aiService from "@/lib/ai-service";

export function ConversationSidebar() {
  const {
    conversations, currentConversationId, searchQuery, showArchived,
    setCurrentConversationId, setConversations, setMessages,
    setIsLoadingMessages, setIsLoadingConversations,
    addConversation, updateConversation, removeConversation,
    setSearchQuery, setShowArchived, setError,
  } = useAIStore();

  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameTitle, setRenameTitle] = useState("");

  const fetchConversations = useCallback(async () => {
    setIsLoadingConversations(true);
    try {
      const data = searchQuery
        ? await aiService.searchConversations(searchQuery)
        : await aiService.getConversations();
      setConversations(data);
    } catch {
      setError("Failed to load conversations");
    } finally {
      setIsLoadingConversations(false);
    }
  }, [searchQuery, setConversations, setIsLoadingConversations, setError]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleNewConversation = async () => {
    try {
      const conv = await aiService.createConversation();
      addConversation(conv);
      setCurrentConversationId(conv.id);
      setMessages([]);
    } catch {
      setError("Failed to create conversation");
    }
  };

  const handleSelectConversation = async (id: string) => {
    setCurrentConversationId(id);
    setIsLoadingMessages(true);
    try {
      const conv = await aiService.getConversation(id);
      setMessages(conv.messages || []);
    } catch {
      setError("Failed to load conversation");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const handleTogglePin = async (e: React.MouseEvent, id: string, isPinned: boolean) => {
    e.stopPropagation();
    try {
      await aiService.updateConversation(id, { is_pinned: !isPinned });
      updateConversation(id, { is_pinned: !isPinned });
    } catch {
      // silently fail
    }
  };

  const handleToggleArchive = async (e: React.MouseEvent, id: string, isArchived: boolean) => {
    e.stopPropagation();
    try {
      await aiService.updateConversation(id, { is_archived: !isArchived });
      if (!showArchived) {
        removeConversation(id);
      } else {
        updateConversation(id, { is_archived: !isArchived });
      }
    } catch {
      // silently fail
    }
  };

  const handleRenameStart = (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    setRenameId(id);
    setRenameTitle(title);
  };

  const handleRenameEnd = async () => {
    if (renameId && renameTitle.trim()) {
      try {
        await aiService.updateConversation(renameId, { title: renameTitle.trim() });
        updateConversation(renameId, { title: renameTitle.trim() });
      } catch {
        // silently fail
      }
    }
    setRenameId(null);
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await aiService.deleteConversation(id);
      removeConversation(id);
    } catch {
      setError("Failed to delete conversation");
    }
  };

  const filteredConversations = conversations.filter((c) => {
    const matchesSearch = searchQuery
      ? c.title.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    const matchesArchive = showArchived ? true : !c.is_archived;
    return matchesSearch && matchesArchive;
  });

  const pinned = filteredConversations.filter((c) => c.is_pinned);
  const unpinned = filteredConversations.filter((c) => !c.is_pinned);

  return (
    <div className="flex h-full flex-col border-r bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-sm font-semibold">Conversations</h2>
        <button
          type="button"
          onClick={handleNewConversation}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          title="New conversation"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </button>
      </div>

      <div className="border-b px-3 py-2">
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-full rounded-lg border bg-background pl-8 pr-3 text-xs outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {filteredConversations.length === 0 && (
            <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
              <svg className="h-8 w-8 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
              </svg>
              <p className="text-xs text-muted-foreground">
                {searchQuery ? "No conversations found" : "No conversations yet"}
              </p>
            </div>
          )}

          {pinned.length > 0 && (
            <div className="px-3 pt-3 pb-1">
              <p className="text-[10px] font-medium uppercase text-muted-foreground">Pinned</p>
              {pinned.map((conv) => (
                <motion.div
                  key={conv.id}
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  layout
                >
                  <SidebarItem
                    conv={conv}
                    isActive={conv.id === currentConversationId}
                    renameId={renameId}
                    renameTitle={renameTitle}
                    onSelect={handleSelectConversation}
                    onTogglePin={handleTogglePin}
                    onToggleArchive={handleToggleArchive}
                    onRenameStart={handleRenameStart}
                    onRenameEnd={handleRenameEnd}
                    onRenameTitleChange={setRenameTitle}
                    onDelete={handleDelete}
                  />
                </motion.div>
              ))}
            </div>
          )}

          <div className="px-3 pt-3 pb-1">
            {pinned.length > 0 && unpinned.length > 0 && (
              <p className="text-[10px] font-medium uppercase text-muted-foreground">Recent</p>
            )}
            {unpinned.map((conv) => (
              <motion.div key={conv.id} layout>
                <SidebarItem
                  conv={conv}
                  isActive={conv.id === currentConversationId}
                  renameId={renameId}
                  renameTitle={renameTitle}
                  onSelect={handleSelectConversation}
                  onTogglePin={handleTogglePin}
                  onToggleArchive={handleToggleArchive}
                  onRenameStart={handleRenameStart}
                  onRenameEnd={handleRenameEnd}
                  onRenameTitleChange={setRenameTitle}
                  onDelete={handleDelete}
                />
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>

      <div className="border-t px-3 py-2">
        <button
          type="button"
          onClick={() => setShowArchived(!showArchived)}
          className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs transition-colors ${
            showArchived ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/50"
          }`}
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m10 6.25h-3.5M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
          {showArchived ? "Hide Archived" : "Show Archived"}
        </button>
      </div>
    </div>
  );
}

interface SidebarItemProps {
  conv: aiService.Conversation;
  isActive: boolean;
  renameId: string | null;
  renameTitle: string;
  onSelect: (id: string) => void;
  onTogglePin: (e: React.MouseEvent, id: string, isPinned: boolean) => void;
  onToggleArchive: (e: React.MouseEvent, id: string, isArchived: boolean) => void;
  onRenameStart: (e: React.MouseEvent, id: string, title: string) => void;
  onRenameEnd: () => void;
  onRenameTitleChange: (title: string) => void;
  onDelete: (e: React.MouseEvent, id: string) => void;
}

function SidebarItem({
  conv, isActive, renameId, renameTitle,
  onSelect, onTogglePin, onToggleArchive, onRenameStart,
  onRenameEnd, onRenameTitleChange, onDelete,
}: SidebarItemProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(conv.id)}
      className={`group mb-0.5 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-colors ${
        isActive
          ? "bg-accent text-accent-foreground"
          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
      }`}
    >
      {renameId === conv.id ? (
        <input
          type="text"
          value={renameTitle}
          onChange={(e) => onRenameTitleChange(e.target.value)}
          onBlur={onRenameEnd}
          onKeyDown={(e) => {
            if (e.key === "Enter") onRenameEnd();
            if (e.key === "Escape") onRenameEnd();
          }}
          className="flex-1 rounded border bg-background px-1.5 py-0.5 text-xs outline-none focus:ring-1 focus:ring-primary"
          autoFocus
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="flex-1 truncate">
          {conv.is_archived && (
            <svg className="mr-1 inline-block h-3 w-3 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m10 6.25h-3.5" />
            </svg>
          )}
          {conv.title || "New Conversation"}
        </span>
      )}

      <div className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          type="button"
          onClick={(e) => onTogglePin(e, conv.id, !!conv.is_pinned)}
          className={`rounded p-0.5 ${
            conv.is_pinned ? "text-primary" : "text-muted-foreground hover:text-foreground"
          }`}
          title={conv.is_pinned ? "Unpin" : "Pin"}
        >
          <svg className="h-3.5 w-3.5" fill={conv.is_pinned ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
          </svg>
        </button>

        <button
          type="button"
          onClick={(e) => onToggleArchive(e, conv.id, !!conv.is_archived)}
          className="rounded p-0.5 text-muted-foreground hover:text-foreground"
          title={conv.is_archived ? "Unarchive" : "Archive"}
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
        </button>

        <button
          type="button"
          onClick={(e) => onRenameStart(e, conv.id, conv.title)}
          className="rounded p-0.5 text-muted-foreground hover:text-foreground"
          title="Rename"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
          </svg>
        </button>

        <button
          type="button"
          onClick={(e) => onDelete(e, conv.id)}
          className="rounded p-0.5 text-muted-foreground hover:text-destructive"
          title="Delete"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
        </button>
      </div>
    </button>
  );
}
