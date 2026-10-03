import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", () => ({
  default: {
    post: vi.fn(async () => ({ data: { id: "d1" } })),
  },
}));

import apiClient from "@/lib/api-client";
import { uploadDocument } from "@/lib/document-service";

function pdfFile(): File {
  return new File(["%PDF-1.4 fake"], "notes.pdf", { type: "application/pdf" });
}

describe("uploadDocument course association (P0.2)", () => {
  it("omits subject_id when no course is chosen", async () => {
    await uploadDocument(pdfFile());
    const post = vi.mocked(apiClient.post);
    expect(post).toHaveBeenCalledTimes(1);
    const formData = post.mock.calls[0][1] as FormData;
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get("subject_id")).toBeNull();
    expect((formData.get("file") as File).name).toBe("notes.pdf");
  });

  it("appends subject_id when a course is chosen", async () => {
    vi.mocked(apiClient.post).mockClear();
    await uploadDocument(pdfFile(), "11111111-2222-3333-4444-555555555555");
    const post = vi.mocked(apiClient.post);
    const formData = post.mock.calls[0][1] as FormData;
    expect(formData.get("subject_id")).toBe("11111111-2222-3333-4444-555555555555");
  });
});
