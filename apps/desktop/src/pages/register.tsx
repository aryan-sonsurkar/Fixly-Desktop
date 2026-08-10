import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";
import { AuthLayout } from "@/components/auth-layout";
import { createLogger } from "@/lib/logger";
import { Button, Input, Label, Separator } from "@fixly/ui";
import { listProfiles, restoreProfile, setTokens, type SavedProfileSummary } from "@/lib/secure-storage";
import apiClient from "@/lib/api-client";

const logger = createLogger("register-page");

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
});

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { signUp, isAuthenticated } = useAuth();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [error, setError] = useState<string | null>(null);
  const [googleState, setGoogleState] = useState<"idle" | "waiting" | "error">("idle");
  const [profiles, setProfiles] = useState<SavedProfileSummary[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "" },
  });

  useEffect(() => {
    let cancelled = false;
    listProfiles().then((p) => {
      if (!cancelled) setProfiles(p);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Already signed in? Go straight to the dashboard.
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const continueAsProfile = async (email: string) => {
    setError(null);
    try {
      const tokens = await restoreProfile(email);
      if (!tokens) {
        setError("Saved session expired for this profile. Create a new account instead.");
        return;
      }
      const response = await apiClient.post("/api/v1/auth/refresh", {
        refresh_token: tokens.refreshToken,
      });
      const data = response.data;
      setAuth(data.access_token, data.user);
      await setTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      logger.error("Failed to restore profile", err);
      setError("Could not restore this profile. Please create a new account.");
    }
  };

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    try {
      // No password: account creation auto-logs you in. Your data stays
      // separate from every other account.
      await signUp(data.email, undefined, data.name);
      if (!isAuthenticated) {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { error?: string } } };
      const message =
        axiosError?.response?.data?.error ||
        (err instanceof Error && err.message ? err.message : "Could not create account. Please check your connection and try again.");
      setError(message);
      logger.error("Registration failed", err);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setGoogleState("waiting");
    try {
      const { getGoogleAuthUrl } = await import("@/lib/auth-service");
      const url = await getGoogleAuthUrl();
      const isTauri =
        typeof window !== "undefined" &&
        (window as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
      if (isTauri) {
        const { open } = await import("@tauri-apps/plugin-shell");
        await open(url);
      } else {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    } catch (err) {
      logger.error("Google sign-in failed to start", err);
      setGoogleState("error");
      setError("Could not start Google sign-in. Please try again.");
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Set up Fixly in seconds — no password needed"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="space-y-2">
          <Label htmlFor="name">Full name</Label>
          <Input
            id="name"
            type="text"
            placeholder="John Doe"
            autoComplete="name"
            autoFocus
            {...register("name")}
          />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating your workspace..." : "Create account"}
        </Button>

        {profiles.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Previously used on this device:</p>
            {profiles.map((p) => (
              <Button
                key={p.email}
                type="button"
                variant="outline"
                className="w-full justify-start text-sm"
                onClick={() => continueAsProfile(p.email)}
              >
                <span className="truncate">{p.name}</span>
                <span className="ml-auto truncate text-xs text-muted-foreground">{p.email}</span>
              </Button>
            ))}
          </div>
        )}

        <div className="relative my-6">
          <Separator />
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
            or continue with
          </span>
        </div>

        {googleState === "waiting" && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground"
          >
            Waiting for Google sign-in in your browser… return to Fixly when you're done.
          </motion.p>
        )}

        <Button
          type="button"
          variant="outline"
          className="w-full"
          disabled={googleState === "waiting"}
          onClick={handleGoogleLogin}
        >
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
          {googleState === "waiting" ? "Opening browser…" : "Continue with Google"}
        </Button>
      </form>
    </AuthLayout>
  );
}