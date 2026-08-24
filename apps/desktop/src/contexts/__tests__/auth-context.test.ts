import { describe, expect, it } from "vitest";
import { isAuthDeepLink } from "@/contexts/auth-context";

describe("auth deep links", () => {
  it("recognizes Tauri callback URLs", () => {
    expect(isAuthDeepLink(new URL("fixly://auth/callback?code=abc"))).toBe(true);
    expect(isAuthDeepLink(new URL("fixly://auth/verified?token=abc"))).toBe(true);
  });

  it("does not treat unrelated URLs as auth callbacks", () => {
    expect(isAuthDeepLink(new URL("fixly://dashboard"))).toBe(false);
    expect(isAuthDeepLink(new URL("https://example.com/auth/callback"))).toBe(true);
  });
});