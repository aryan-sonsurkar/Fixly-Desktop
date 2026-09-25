import { describe, expect, it, vi } from "vitest";
import axios from "axios";
import { stripJsonContentTypeForFormData } from "@/lib/api-client";

describe("axios dispatch preserves FormData (regression: 50MB false error)", () => {
  it("default JSON Content-Type destroys FormData without the guard", async () => {
    // Documents the exact production bug: axios transformRequest stringifies
    // FormData when merged headers contain application/json.
    let seen: unknown;
    const client = axios.create({
      headers: { "Content-Type": "application/json" },
      adapter: async (config) => {
        seen = config.data;
        return {
          data: {}, status: 200, statusText: "OK", headers: {}, config,
        } as never;
      },
    });
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4"]), "a.pdf");
    await client.post("http://127.0.0.1:9/api/v1/documents/upload", form);
    // Without the interceptor guard the adapter receives a JSON string.
    expect(typeof seen).toBe("string");
  });

  it("stripJsonContentTypeForFormData keeps FormData intact through dispatch", async () => {
    // NOTE: axios itself sets urlencoded Content-Type pre-adapter
    // (dispatchRequest). That is expected and harmless: the fetch-based
    // adapter strips any Content-Type for FormData so the transport
    // generates the correct multipart boundary (covered by adapter tests).
    let seen: unknown;
    const client = axios.create({
      headers: { "Content-Type": "application/json" },
      adapter: async (config) => {
        seen = config.data;
        return {
          data: {}, status: 200, statusText: "OK", headers: {}, config,
        } as never;
      },
    });
    client.interceptors.request.use((config) => {
      stripJsonContentTypeForFormData(config);
      return config;
    });
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4"]), "a.pdf");
    await client.post("http://127.0.0.1:9/api/v1/documents/upload", form);
    expect(seen).toBeInstanceOf(FormData);
  });

  it("leaves JSON payloads untouched", () => {
    const headers = { "Content-Type": "application/json", other: 1 };
    stripJsonContentTypeForFormData({ data: { a: 1 }, headers } as never);
    expect(headers["Content-Type"]).toBe("application/json");
    const plain: Record<string, unknown> = {};
    stripJsonContentTypeForFormData({ data: new FormData(), headers: plain } as never);
    expect(plain).toEqual({});
  });

  it("strip function is a no-op for non-FormData", () => {
    const spy = vi.fn();
    stripJsonContentTypeForFormData({ data: "x", headers: { delete: spy } } as never);
    expect(spy).not.toHaveBeenCalled();
  });
});
