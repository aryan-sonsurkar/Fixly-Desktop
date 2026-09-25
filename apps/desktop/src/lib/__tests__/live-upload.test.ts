import { describe, expect, it, vi } from "vitest";

// Live contract test: proves the full axios pipeline (interceptors +
// transforms + fetch adapter) delivers a parseable multipart body that
// reaches FastAPI's `file` field. Self-skipping: runs against a backend at
// VITE_API_URL (or :18080 fallback) when one answers, skips otherwise.
const LIVE_URL =
  (globalThis as { process?: { env?: Record<string, string> } }).process?.env?.VITE_API_URL ||
  "http://127.0.0.1:18080";

async function backendReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${LIVE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

describe("live upload contract", () => {
  it("multipart body parses server-side (401 means parsed, 422 means malformed)", async () => {
    if (!(await backendReachable())) {
      console.log("LIVE backend not reachable at", LIVE_URL, "- skipping");
      return;
    }
    vi.stubEnv("VITE_API_URL", LIVE_URL);
    const { default: apiClient } = await import("@/lib/api-client");
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4 hello"]), "probe.pdf");
    // No token: a well-formed request must fail at AUTH (401), never at
    // multipart parsing (422). 422 here = client serialization bug.
    const err = await apiClient.post("/api/v1/documents/upload", form).catch((e) => e);
    const status = err?.response?.status;
    expect(status).toBe(401);
  });
});
