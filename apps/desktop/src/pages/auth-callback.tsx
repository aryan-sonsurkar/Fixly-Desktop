import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { AuthLayout } from "@/components/auth-layout";
import { useAuthStore } from "@/stores/auth-store";
import { setTokens } from "@/lib/secure-storage";
import { createLogger } from "@/lib/logger";
import { Button } from "@fixly/ui";

const logger = createLogger("auth-callback-page");

export function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const params = useParams();
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    async function handleCallback() {
      try {
        // Handle email verification callback (from Supabase redirect)
        const verified = searchParams.get("verified");
        const token = searchParams.get("token");
        
        if (verified === "true" && token) {
          // Email verification successful
          // In development, we can just redirect to login
          setStatus("success");
          setMessage("Email verified successfully! Redirecting to login...");
          setTimeout(() => navigate("/login"), 2000);
          return;
        }

        // Handle OAuth callback (Google, etc.) - tokens in hash fragment
        const hash = window.location.hash.substring(1);
        const hashParams = new URLSearchParams(hash);
        const accessToken = hashParams.get("access_token");
        const refreshToken = hashParams.get("refresh_token");
        const error = searchParams.get("error") || hashParams.get("error");

        if (error) {
          throw new Error(error);
        }

        if (accessToken && refreshToken) {
          // Store tokens
          await setTokens({ accessToken, refreshToken });
          
          // Get user info
          const apiClient = (await import("@/lib/api-client")).default;
          const response = await apiClient.get("/api/v1/auth/me", {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          
          const user = response.data;
          setAuth(accessToken, user);
          
          setStatus("success");
          setMessage("Sign in successful! Redirecting to dashboard...");
          setTimeout(() => navigate("/dashboard", { replace: true }), 1500);
          return;
        }

        // No tokens found - might be an error or different flow
        if (params.error) {
          throw new Error(params.error_description || params.error);
        }

        // If we reach here without tokens or verified flag, redirect to login
        navigate("/login?error=callback_failed");
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Authentication failed";
        logger.error("Auth callback error", err);
        setStatus("error");
        setMessage(message);
      }
    }

    handleCallback();
  }, []);

  if (status === "loading") {
    return (
      <AuthLayout title="Processing..." subtitle="Please wait">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-6 text-center"
        >
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <svg
              className="h-8 w-8 text-primary animate-spin"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
          <p className="text-sm text-muted-foreground">Completing authentication...</p>
        </motion.div>
      </AuthLayout>
    );
  }

  if (status === "error") {
    return (
      <AuthLayout title="Authentication Failed" subtitle="Something went wrong">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-6 text-center"
        >
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
            <svg
              className="h-8 w-8 text-destructive"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div className="space-y-2">
            <p className="text-sm text-foreground">Authentication failed</p>
            <p className="text-xs text-muted-foreground">{message}</p>
          </div>
          <Button onClick={() => window.location.href = "/login"} className="w-full">
            Return to Login
          </Button>
        </motion.div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Success" subtitle="Authentication complete">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-6 text-center"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
          <svg
            className="h-8 w-8 text-success"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div className="space-y-2">
          <p className="text-sm text-foreground">{message}</p>
        </div>
      </motion.div>
    </AuthLayout>
  );
}