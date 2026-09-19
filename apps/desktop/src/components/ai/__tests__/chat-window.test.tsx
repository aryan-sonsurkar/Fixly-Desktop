import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAIStore } from "@/stores/ai-store";
import { ChatWindow } from "@/components/ai/chat-window";

vi.mock("@/lib/ai-service", () => ({
  sendChatStream: vi.fn(),
  sendChat: vi.fn(),
  deleteMessage: vi.fn(),
  setMessageFeedback: vi.fn(),
  editMessage: vi.fn(),
  deleteConversation: vi.fn(),
  createConversation: vi.fn(),
}));

import * as aiService from "@/lib/ai-service";

if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => undefined;
}

describe("ChatWindow failure and retry", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAIStore.getState().reset();
    useAIStore.getState().setSettings({
      preferred_provider: "fixly-local",
      provider_model: null,
      temperature: 0.7,
      max_tokens: 1024,
      streaming_enabled: true,
      system_prompt: null,
      ollama_available: false,
      gemini_available: false,
    });
    useAIStore.getState().setCurrentConversationId("conv-1");
    useAIStore.getState().setMessages([]);
  });

  it("shows inline error with Try again after a failed send", async () => {
    (aiService.sendChatStream as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Fixly AI is currently unavailable. Please try again in a moment."),
    );
    render(<ChatWindow />);
    fireEvent.change(screen.getByPlaceholderText("Ask Fixly anything..."), {
      target: { value: "Hello" },
    });
    fireEvent.click(screen.getByRole("button", { name: "" }));
    await waitFor(() => {
      expect(screen.getByText("Fixly couldn't complete that response.")).toBeTruthy();
    });
    expect(screen.getByText("Try again")).toBeTruthy();
  });

  it("Try again resends the failed prompt", async () => {
    const send = aiService.sendChatStream as unknown as ReturnType<typeof vi.fn>;
    send.mockRejectedValueOnce(new Error("boom"));
    send.mockResolvedValueOnce({
      message: { id: "m1", conversation_id: "conv-1", role: "assistant", content: "Hi!", created_at: new Date().toISOString() },
      conversation: { id: "conv-1", title: "Hello", created_at: "", updated_at: "" },
    });
    render(<ChatWindow />);
    fireEvent.change(screen.getByPlaceholderText("Ask Fixly anything..."), {
      target: { value: "Hello" },
    });
    fireEvent.click(screen.getByRole("button", { name: "" }));
    await waitFor(() => {
      expect(screen.getByText("Try again")).toBeTruthy();
    });
    fireEvent.click(screen.getByText("Try again"));
    await waitFor(() => {
      expect(send).toHaveBeenCalledTimes(2);
    });
    expect(send.mock.calls[1][0]).toMatchObject({ message: "Hello" });
  });
});
