import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

type MockAdapter = (config: never) => Promise<{ status: number; data: unknown }>;

vi.mock("@tauri-apps/plugin-http", () => ({
  fetch: vi.fn(),
}));

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

function makeResponse(status: number, body: unknown) {
  return {
    status,
    statusText: "",
    text: async () => JSON.stringify(body),
    headers: { forEach() {} },
  };
}

function setTauriWindow() {
  (globalThis as { window?: unknown }).window = { __TAURI_INTERNALS__: {} } as never;
}

function clearTauriWindow() {
  delete (globalThis as { window?: unknown }).window;
}

describe("Tauri HTTP adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
    clearTauriWindow();
  });

  it("rejects non-2xx responses with the backend error payload attached", async () => {
    const { fetch } = await import("@tauri-apps/plugin-http");
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeResponse(401, { error: "An account with this email already exists.", code: "UNAUTHORIZED", status: 401 }),
    );

    const { createTauriAdapter } = await import("@/lib/api-client");
    const adapter = (await createTauriAdapter()) as unknown as MockAdapter;
    const config = {
      url: "/api/v1/auth/signup",
      baseURL: "http://127.0.0.1:9999",
      method: "post",
      headers: {},
      data: { email: "a@b.com", password: "Secret123" },
    };

    await expect(adapter(config as never)).rejects.toMatchObject({
      response: {
        status: 401,
        data: { error: "An account with this email already exists." },
      },
    });
  });

  it("resolves successful responses", async () => {
    const { fetch } = await import("@tauri-apps/plugin-http");
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeResponse(200, { access_token: "abc" }),
    );

    const { createTauriAdapter } = await import("@/lib/api-client");
    const adapter = (await createTauriAdapter()) as unknown as MockAdapter;
    const config = {
      url: "/api/v1/auth/signin",
      baseURL: "http://127.0.0.1:9999",
      method: "post",
      headers: {},
      data: { email: "a@b.com", password: "Secret123" },
    };

    const response = await adapter(config as never);
    expect(response.status).toBe(200);
    expect(response.data).toEqual({ access_token: "abc" });
  });

  it("passes FormData uploads through without JSON-encoding or manual Content-Type", async () => {
    const { fetch } = await import("@tauri-apps/plugin-http");
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeResponse(200, { id: "doc-1" }),
    );

    const { createTauriAdapter } = await import("@/lib/api-client");
    const adapter = (await createTauriAdapter()) as unknown as MockAdapter;
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4"], { type: "application/pdf" }), "notes.pdf");
    const config = {
      url: "/api/v1/documents/upload",
      baseURL: "http://127.0.0.1:9999",
      method: "post",
      // A manually set multipart header without boundary must not survive:
      // the browser-generated boundary is required for FastAPI to parse.
      headers: { "Content-Type": "multipart/form-data" },
      data: form,
    };

    await adapter(config as never);

    const calls = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    const init = calls[0][1] as { body?: unknown; headers?: Record<string, string> };
    expect(init.body).toBe(form);
    expect(init.headers?.["Content-Type"]).toBeUndefined();
  });

  it("uses native webview fetch for FormData so its multipart boundary is preserved", async () => {
    const { fetch: pluginFetch } = await import("@tauri-apps/plugin-http");
    const { invoke } = await import("@tauri-apps/api/core");
    (invoke as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(9999);
    const nativeFetch = vi.fn().mockResolvedValue(makeResponse(200, { id: "doc-1" }));
    vi.stubGlobal("window", {
      __TAURI_INTERNALS__: {},
      fetch: nativeFetch,
    });

    const { createTauriAdapter } = await import("@/lib/api-client");
    const adapter = (await createTauriAdapter()) as unknown as MockAdapter;
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4"], { type: "application/pdf" }), "notes with spaces.pdf");

    await adapter({
      url: "/api/v1/documents/upload",
      baseURL: "http://127.0.0.1:9999",
      method: "post",
      headers: { "Content-Type": "multipart/form-data" },
      data: form,
    } as never);

    expect(nativeFetch).toHaveBeenCalledOnce();
    expect(pluginFetch).not.toHaveBeenCalled();
    const init = nativeFetch.mock.calls[0][1] as { body?: unknown; headers?: Record<string, string> };
    expect(init.body).toBe(form);
    expect(init.headers?.["Content-Type"]).toBeUndefined();
  });

  it("resolves the backend port from Rust and targets it for requests", async () => {
    const { invoke } = await import("@tauri-apps/api/core");
    (invoke as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(12345);

    const { fetch } = await import("@tauri-apps/plugin-http");
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(makeResponse(200, { ok: true }));

    setTauriWindow();

    const { createTauriAdapter, ensureBackendPort } = await import("@/lib/api-client");
    const port = await ensureBackendPort();
    expect(port).toBe(12345);

    const adapter = (await createTauriAdapter()) as unknown as MockAdapter;
    const config = { url: "/api/v1/auth/me", method: "get", headers: {} };
    await adapter(config as never);

    const calls = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(String(calls[0][0])).toContain("127.0.0.1:12345");
  });
});
