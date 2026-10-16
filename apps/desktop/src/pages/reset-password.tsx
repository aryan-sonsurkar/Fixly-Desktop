import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AuthLayout } from "@/components/auth-layout";
import { Button, Input, Label } from "@fixly/ui";
import { createLogger } from "@/lib/logger";

const logger = createLogger("reset-password-page");

/**
 * Set a new password from a recovery token.
 *
 * Accepts the token three ways (first one found wins):
 * 1. `?token=` query param (Supabase PKCE `token_hash`, pasted links),
 * 2. `#access_token=` URL hash (Supabase implicit recovery links),
 * 3. manual paste into the token field (works even when deep links fail).
 */
export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "sending" | "done">("idle");

  useEffect(() => {
    const fromQuery =
      searchParams.get("token") || searchParams.get("token_hash") || searchParams.get("access_token");
    if (fromQuery) {
      setToken(fromQuery);
      return;
    }
    const hash = window.location.hash.startsWith("#") ? window.location.hash.substring(1) : "";
    const accessToken = new URLSearchParams(hash).get("access_token");
    if (accessToken) setToken(accessToken);
  }, [searchParams]);

  const handleReset = async () => {
    setError(null);
    if (!token.trim()) {
      setError("Paste the recovery token from your reset email first.");
      return;
    }
    if (password.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setStatus("sending");
    try {
      const { resetPassword } = await import("@/lib/auth-service");
      await resetPassword(token.trim(), password);
      setStatus("done");
    } catch (err: unknown) {
      logger.error("Reset password failed", err);
      setStatus("idle");
      const axiosErr = err as { response?: { data?: { error?: string } } };
      setError(
        axiosErr?.response?.data?.error ||
          "Could not reset the password. The link may have expired — request a fresh one from Sign in → Forgot password?"
      );
    }
  };

  return (
    <AuthLayout title="Set a new password" subtitle="From your recovery email">
      <div className="space-y-4">
        {status === "done" ? (
          <div className="space-y-4 text-center">
            <p className="text-sm text-green-600 dark:text-green-400">
              Password updated. Sign in with your new password.
            </p>
            <Button className="w-full" onClick={() => navigate("/register")}>
              Back to sign in
            </Button>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="recovery-token">Recovery token</Label>
              <Input
                id="recovery-token"
                type="text"
                placeholder="Paste from your reset email if not prefilled"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                placeholder="At least 8 characters"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm new password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="Repeat your new password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
            <Button className="w-full" disabled={status === "sending"} onClick={() => void handleReset()}>
              {status === "sending" ? "Updating…" : "Set new password"}
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              <button type="button" onClick={() => navigate("/register")} className="underline font-medium text-primary">
                Back to sign in
              </button>
            </p>
          </>
        )}
      </div>
    </AuthLayout>
  );
}
