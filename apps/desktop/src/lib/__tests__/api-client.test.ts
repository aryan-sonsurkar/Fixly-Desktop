import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

type MockAdapter = (config: never) => Promise<{ status: number; data: unknown }>;

vi.mock("@tauri-apps/plugin-http", () => ({
  fetch: vi.fn(),
}));

function makeResponse(status: number, body: unknown) {
  return {
    status,
    statusText: "",
    text: async () => JSON.stringify(body),
    headers: { forEach() {} },
  };
}

describe("Tauri HTTP adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetModules();
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
});