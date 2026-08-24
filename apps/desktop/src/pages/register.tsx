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
const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().optional(),
});

type RegisterForm = z.infer<typeof registerSchema>;
type LoginForm = z.infer<typeof loginSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { signUp, signIn, isAuthenticated } = useAuth();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<"signup" | "signin">("signup");
  const [error, setError] = useState<string | null>(null);
  const [googleState, setGoogleState] = useState<"idle" | "waiting" | "error">("idle");
  const [googleEnabled, setGoogleEnabled] = useState<boolean | null>(null);
  const [googleReason, setGoogleReason] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<SavedProfileSummary[]>([]);
  const [autoLoginAttempted, setAutoLoginAttempted] = useState(false);

  const combinedSchema = mode === "signup" ? registerSchema : loginSchema;
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm | LoginForm>({
    // Re-create resolver when mode changes via key on form element is simpler than dynamic resolver – use shouldUnregister + manual check
    resolver: zodResolver(combinedSchema as unknown as typeof registerSchema),
    defaultValues: mode === "signup" ? ({ name: "", email: "" } as RegisterForm) : ({ email: "", password: "" } as unknown as RegisterForm),
  });

  const switchMode = (next: "signup" | "signin") => {
    setMode(next);
    setError(null);
    // Reset with next mode defaults; resolver will be re-evaluated on next render via combinedSchema
    reset(next === "signup" ? ({ name: "", email: "" } as unknown as RegisterForm) : ({ email: "", password: "" } as unknown as RegisterForm));
  };

  useEffect(() => {
    let cancelled = false;
    listProfiles().then((p) => {
      if (!cancelled) setProfiles(p);
    });
    // Probe Google OAuth availability without blocking render
    (async () => {
      try {
        const { getGoogleAuthStatus } = await import("@/lib/auth-service");
        const s = await getGoogleAuthStatus();
        if (!cancelled) {
          setGoogleEnabled(s.enabled);
          setGoogleReason(s.reason || null);
        }
      } catch {
        if (!cancelled) setGoogleEnabled(false);
      }
    })();
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

  // Auto-login: if single saved profile exists and user arrived logged-out,
  // try silent refresh to avoid extra click (perceived instant)
  useEffect(() => {
    if (isAuthenticated || autoLoginAttempted || profiles.length !== 1) return;
    // don't auto if error already shown
    const email = profiles[0].email;
    setAutoLoginAttempted(true);
    // small delay so UI paints first
    const t = setTimeout(() => {
      void continueAsProfile(email);
    }, 400);
    return () => clearTimeout(t);
  }, [profiles, isAuthenticated, autoLoginAttempted]);

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

  const onSubmit = async (data: RegisterForm | LoginForm) => {
    setError(null);
    try {
      if (mode === "signin") {
        const loginData = data as LoginForm;
        // Prefer saved profile silent login if available on this device
        const profileMatch = profiles.find((p) => p.email.toLowerCase() === loginData.email.toLowerCase());
        if (profileMatch) {
          await continueAsProfile(loginData.email);
          return;
        }
        // Fallback to password sign-in (if user set a password) or helpful error
        if (loginData.password) {
          await signIn(loginData.email, loginData.password);
        } else {
          // Try passwordless sign-in path: inform user to use saved profile or create
          throw new Error("No saved session for this email on this device. If you created this account here before, use 'Previously used' below. Otherwise create a new account with a different email or set a password.");
        }
        navigate("/dashboard", { replace: true });
        return;
      }
      // signup
      const regData = data as RegisterForm;
      await signUp(regData.email, undefined, regData.name);
      if (!isAuthenticated) {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { error?: string } } };
      const raw =
        axiosError?.response?.data?.error ||
        (err instanceof Error && err.message ? err.message : "Could not create account. Please check your connection and try again.");
      // If already exists in signup mode, offer switch to sign-in
      if (raw.toLowerCase().includes("already exists") && mode === "signup") {
        const typed = (data as RegisterForm).email;
        const hasProfile = profiles.some((p) => p.email.toLowerCase() === typed.toLowerCase());
        setError(
          hasProfile
            ? `An account with ${typed} already exists on this device. Tap the saved profile below to sign in instantly.`
            : `An account with ${typed} already exists. Switch to Sign in below, or use a different email.`
        );
        // Keep email prefilled when switching
        if (!hasProfile) setMode("signin");
        logger.error("Registration failed - already exists", err);
        return;
      }
      setError(raw);
      logger.error(mode === "signin" ? "Sign-in failed" : "Registration failed", err);
    }
  };

  const handleGoogleLogin = async () => {
    if (googleEnabled === false) {
      setError(googleReason || "Google sign-in is not available. Please use email or create an account above.");
      return;
    }
    setError(null);
    setGoogleState("waiting");
    try {
      const { getGoogleAuthUrl } = await import("@/lib/auth-service");
      // For Tauri deep-link is fixly://auth/callback, for web use current origin
      const isTauri =
        typeof window !== "undefined" &&
        (window as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
      const redirectTo = isTauri ? "fixly://auth/callback" : `${window.location.origin}/auth/callback`;
      const url = await getGoogleAuthUrl(redirectTo);
      if (isTauri) {
        const { open } = await import("@tauri-apps/plugin-shell");
        await open(url);
      } else {
        window.open(url, "_blank", "noopener,noreferrer");
      }
      // Reset waiting after 30s if no callback
      setTimeout(() => setGoogleState((s) => (s === "waiting" ? "idle" : s)), 30000);
    } catch (err: unknown) {
      logger.error("Google sign-in failed to start", err);
      setGoogleState("error");
      const axiosErr = err as { response?: { data?: { error?: string } } };
      const msg =
        axiosErr?.response?.data?.error ||
        (err instanceof Error ? err.message : null) ||
        "Could not start Google sign-in.";
      // Surface redirect_uri_mismatch helpfully
      if (msg.toLowerCase().includes("redirect_uri") || msg.toLowerCase().includes("redirect")) {
        setError(
          "Google sign-in is misconfigured (redirect_uri_mismatch). Administrator must add fixly://auth/callback and http://localhost:1420/auth/callback to Supabase Auth > URL Configuration and to Google Cloud Console > Authorized redirect URIs (https://<project>.supabase.co/auth/v1/callback). Use email sign-in for now."
        );
      } else if (msg.toLowerCase().includes("not enabled") || msg.toLowerCase().includes("not configured")) {
        setError("Google sign-in is not enabled yet. Please continue with email.");
      } else {
        setError(msg + " Please try again or use email.");
      }
    }
  };

  return (
    <AuthLayout
      title={mode === "signup" ? "Create your account" : "Welcome back"}
      subtitle={mode === "signup" ? "Set up Fixly in seconds — no password needed" : "Sign in to your Fixly workspace"}
    >
      <form key={mode} onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {error}
              {error.toLowerCase().includes("already exists") && (
                <button type="button" onClick={() => switchMode("signin")} className="ml-2 underline font-medium">
                  Sign in instead →
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {mode === "signup" && (
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input
              id="name"
              type="text"
              placeholder="John Doe"
              autoComplete="name"
              autoFocus
              {...register("name" as never)}
            />
            {(errors as unknown as { name?: { message?: string } }).name && (
              <p className="text-xs text-destructive">{(errors as unknown as { name?: { message?: string } }).name?.message}</p>
            )}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            autoFocus={mode === "signin"}
            {...register("email" as never)}
          />
          {(errors as unknown as { email?: { message?: string } }).email && (
            <p className="text-xs text-destructive">{(errors as unknown as { email?: { message?: string } }).email?.message}</p>
          )}
        </div>
        {mode === "signin" && (
          <div className="space-y-2">
            <Label htmlFor="password">Password <span className="text-muted-foreground font-normal">(leave blank if you used passwordless signup)</span></Label>
            <Input id="password" type="password" placeholder="••••••••" autoComplete="current-password" {...register("password" as never)} />
            <p className="text-[11px] text-muted-foreground">Fixly accounts created without a password work via “Previously used on this device”. Use that button below if you see your email there.</p>
          </div>
        )}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? (mode === "signup" ? "Creating your workspace..." : "Signing in...") : mode === "signup" ? "Create account" : "Sign in"}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          {mode === "signup" ? (
            <>Already have an account? <button type="button" onClick={() => switchMode("signin")} className="underline font-medium text-primary">Sign in</button></>
          ) : (
            <>Don’t have an account? <button type="button" onClick={() => switchMode("signup")} className="underline font-medium text-primary">Create account</button></>
          )}
        </p>

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
          disabled={googleState === "waiting" || googleEnabled === false}
          onClick={handleGoogleLogin}
          title={googleEnabled === false ? googleReason || "Google sign-in not configured" : undefined}
        >
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
          {googleState === "waiting" ? "Opening browser…" : googleEnabled === false ? "Continue with Google (unavailable)" : "Continue with Google"}
        </Button>
        {googleEnabled === false && googleReason && (
          <p className="text-[11px] text-muted-foreground text-center">
            {googleReason} – use email above. Admin: enable Google in Supabase Auth and set redirect URIs.
          </p>
        )}
      </form>
    </AuthLayout>
  );
}