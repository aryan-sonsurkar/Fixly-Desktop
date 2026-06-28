import { create } from "zustand";
import type { Conversation, Message, AISettings } from "@/lib/ai-service";

export interface AIState {
  conversations: Conversation[];
  currentConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  error: string | null;
  settings: AISettings | null;
  settingsOpen: boolean;
  infoPanelOpen: boolean;
  searchQuery: string;
  showArchived: boolean;
  editingMessageId: string | null;
  editingContent: string;

  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversationId: (id: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  removeMessage: (id: string) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (content: string) => void;
  setIsLoadingConversations: (loading: boolean) => void;
  setIsLoadingMessages: (loading: boolean) => void;
  setIsSending: (sending: boolean) => void;
  setError: (error: string | null) => void;
  setSettings: (settings: AISettings | null) => void;
  setSettingsOpen: (open: boolean) => void;
  setInfoPanelOpen: (open: boolean) => void;
  setSearchQuery: (query: string) => void;
  setShowArchived: (show: boolean) => void;
  setEditingMessageId: (id: string | null) => void;
  setEditingContent: (content: string) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  removeConversation: (id: string) => void;
  reset: () => void;
}

const initialState = {
  conversations: [],
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: "",
  isLoadingConversations: false,
  isLoadingMessages: false,
  isSending: false,
  error: null,
  settings: null,
  settingsOpen: false,
  infoPanelOpen: false,
  searchQuery: "",
  showArchived: false,
  editingMessageId: null,
  editingContent: "",
};

export const useAIStore = create<AIState>((set) => ({
  ...initialState,

  setConversations: (conversations) => set({ conversations }),
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),
  removeMessage: (id) =>
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== id),
    })),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (content) =>
    set((state) => ({ streamingContent: state.streamingContent + content })),
  setIsLoadingConversations: (loading) => set({ isLoadingConversations: loading }),
  setIsLoadingMessages: (loading) => set({ isLoadingMessages: loading }),
  setIsSending: (sending) => set({ isSending: sending }),
  setError: (error) => set({ error }),
  setSettings: (settings) => set({ settings }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  setInfoPanelOpen: (open) => set({ infoPanelOpen: open }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setShowArchived: (show) => set({ showArchived: show }),
  setEditingMessageId: (id) => set({ editingMessageId: id }),
  setEditingContent: (content) => set({ editingContent: content }),
  addConversation: (conversation) =>
    set((state) => ({ conversations: [conversation, ...state.conversations] })),
  updateConversation: (id, updates) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === id ? { ...c, ...updates } : c,
      ),
    })),
  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id ? null : state.currentConversationId,
      messages: state.currentConversationId === id ? [] : state.messages,
    })),
  reset: () => set(initialState),
}));
