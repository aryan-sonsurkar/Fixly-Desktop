import { describe, expect, it, beforeEach } from "vitest";
import { useAIStore } from "@/stores/ai-store";
import type { Conversation } from "@/lib/ai-service";

function conv(id: string, title = "Test"): Conversation {
  return { id, title, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
}

describe("ai-store conversation handling", () => {
  beforeEach(() => {
    useAIStore.getState().reset();
  });

  it("does not duplicate a conversation added twice", () => {
    const c = conv("c1");
    useAIStore.getState().addConversation(c);
    useAIStore.getState().addConversation(c);
    expect(useAIStore.getState().conversations.filter((x) => x.id === "c1")).toHaveLength(1);
  });

  it("removeConversation clears selection and messages", () => {
    const store = useAIStore.getState();
    store.addConversation(conv("c1"));
    store.setCurrentConversationId("c1");
    store.setMessages([{ id: "m1", conversation_id: "c1", role: "user", content: "hi", created_at: new Date().toISOString() }]);
    useAIStore.getState().removeConversation("c1");
    const s = useAIStore.getState();
    expect(s.conversations).toHaveLength(0);
    expect(s.currentConversationId).toBeNull();
    expect(s.messages).toHaveLength(0);
  });
});
