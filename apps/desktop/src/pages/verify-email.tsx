import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { AuthLayout } from "@/components/auth-layout";
import { resendVerification } from "@/lib/auth-service";
import { useAuthStore } from "@/stores/auth-store";
import { createLogger } from "@/lib/logger";
import { Button } from "@fixly/ui";

const logger = createLogger("verify-email-page");

export function VerifyEmailPage() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const navigate = useNavigate();
  const [resent, setResent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleResend = async () => {
    if (!user?.email || sending) return;
    setSending(true);
    setError(null);
    try {
      await resendVerification(user.email);
      if (!mountedRef.current) return;
      setResent(true);
      setTimeout(() => { if (mountedRef.current) setResent(false); }, 60000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Could not resend verification email.";
      if (mountedRef.current) setError(message);
      logger.error("Resend verification failed", err);
    } finally {
      if (mountedRef.current) setSending(false);
    }
  };

  if (isAuthenticated) {
    return null;
  }

  return (
    <AuthLayout title="Verify your email" subtitle="Almost there! Check your inbox.">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-6 text-center"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <svg
            className="h-8 w-8 text-primary"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            We sent a verification email to{" "}
            <span className="font-medium text-foreground">{user?.email || "your email"}</span>
          </p>
          <p className="text-xs text-muted-foreground">
            Please check your inbox and click the verification link to activate your account.
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-3">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleResend}
            disabled={resent}
          >
            {resent ? "Verification email sent" : "Resend verification email"}
          </Button>

          <p className="text-xs text-muted-foreground">
            Already verified?{" "}
            <Link to="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        <div className="rounded-lg bg-muted/50 p-4">
          <p className="text-xs text-muted-foreground">
            After verification, you can close this page and sign in to your account. If you
            don&apos;t see the email, check your spam folder.
          </p>
        </div>
      </motion.div>
    </AuthLayout>
  );
}
