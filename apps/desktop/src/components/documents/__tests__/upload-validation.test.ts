import { describe, expect, it } from "vitest";
import { checkPickedFile, MAX_SIZE_BYTES } from "@/components/documents/upload-dialog";

function file(name: string, type: string, size: unknown) {
  return { name, type, size } as File;
}

function accept(name: string, type: string, size: unknown) {
  expect(checkPickedFile(file(name, type, size))).toEqual({ ok: true });
}

describe("checkPickedFile", () => {
  it("accepts the known 2.45MB DBMS Notes PDF", () => {
    accept("DSU 13 (25203A0009).pdf", "application/pdf", 2453001);
  });

  it("accepts just under the boundary", () => {
    accept("a.pdf", "application/pdf", MAX_SIZE_BYTES - 1);
    accept("a.pdf", "application/pdf", 49.9 * 1024 * 1024);
  });

  it("accepts exactly 50MB, rejects above", () => {
    accept("a.pdf", "application/pdf", MAX_SIZE_BYTES);
    expect(checkPickedFile(file("a.pdf", "application/pdf", MAX_SIZE_BYTES + 1))).toEqual({
      ok: false,
      reason: "size",
    });
  });

  it("accepts PNG/JPG/WEBP within limit", () => {
    accept("a.png", "image/png", 1024);
    accept("a.jpg", "image/jpeg", 1024);
    accept("a.webp", "image/webp", 1024);
  });

  it("accepts blank Tauri MIME when the extension is supported", () => {
    accept("notes.pdf", "", 2048);
  });

  it("rejects unsupported extension/type", () => {
    expect(checkPickedFile(file("notes.exe", "application/x-msdownload", 2048))).toEqual({
      ok: false,
      reason: "type",
    });
    expect(checkPickedFile(file("notes.txt", "", 2048))).toEqual({ ok: false, reason: "type" });
  });

  it("rejects empty or unreadable sizes", () => {
    expect(checkPickedFile(file("a.pdf", "application/pdf", 0))).toEqual({ ok: false, reason: "empty" });
    expect(checkPickedFile(file("a.pdf", "application/pdf", undefined))).toEqual({ ok: false, reason: "empty" });
    expect(checkPickedFile(file("a.pdf", "application/pdf", Number.NaN))).toEqual({ ok: false, reason: "empty" });
  });

  it("uses bytes consistently (2_453_001 bytes, well under 50 MiB)", () => {
    expect(2453001).toBeLessThan(MAX_SIZE_BYTES);
    expect(MAX_SIZE_BYTES).toBe(50 * 1024 * 1024);
  });
});
