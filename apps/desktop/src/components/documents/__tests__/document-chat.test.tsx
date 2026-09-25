import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DocumentChat } from "@/components/documents/document-chat";

vi.mock("@/lib/document-service", () => ({
  chatWithDocument: vi.fn(),
}));

vi.mock("@/components/ai/markdown-renderer", () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div>{content}</div>,
}));

vi.mock("@/components/ai/source-citations", () => ({
  SourceCitations: () => <div data-testid="citations" />,
}));

import { chatWithDocument } from "@/lib/document-service";

if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => undefined;
}

describe("DocumentChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state with clickable suggestions", () => {
    render(<DocumentChat documentId="d1" docTitle="DBMS Notes.pdf" />);
    expect(screen.getByText("Ask anything about this document.")).toBeTruthy();
    expect(screen.getByText("Summarize this chapter")).toBeTruthy();
  });

  it("sending a suggestion dispatches it and renders the answer", async () => {
    (chatWithDocument as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      message: { id: "m1", content: "Here is a summary.", created_at: new Date().toISOString() },
      conversation: { id: "c1" },
      chunks_used: [{ heading: null, page_number: 3 }],
    });
    render(<DocumentChat documentId="d1" docTitle="DBMS Notes.pdf" />);
    fireEvent.click(screen.getByText("Summarize this chapter"));
    await waitFor(() => {
      expect(screen.getByText("Here is a summary.")).toBeTruthy();
    });
    expect(chatWithDocument).toHaveBeenCalledWith(
      expect.objectContaining({ document_id: "d1", message: "Summarize this chapter" }),
    );
    expect(screen.getByTestId("citations")).toBeTruthy();
  });

  it("shows inline retry on failure without leaking backend text", async () => {
    (chatWithDocument as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("column documents.xyz does not exist"),
    );
    render(<DocumentChat documentId="d1" />);
    fireEvent.change(screen.getByPlaceholderText("Ask about this document..."), {
      target: { value: "Hello" },
    });
    fireEvent.click(screen.getByText("Send"));
    await waitFor(() => {
      expect(screen.getByText("Fixly couldn't complete that response.")).toBeTruthy();
    });
    expect(document.body.textContent).not.toContain("column documents");
    fireEvent.click(screen.getByText("Try again"));
    await waitFor(() => {
      expect(chatWithDocument).toHaveBeenCalledTimes(2);
    });
  });
});
