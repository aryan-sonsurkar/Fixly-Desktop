import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button, Input, Label } from "@fixly/ui";
import { getMySettings, updateMySettings } from "@/lib/profile-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("settings-page");

const settingsSchema = z.object({
  theme: z.enum(["dark", "light", "system"]),
  daily_goal_hours: z.coerce.number().min(0).max(24),
  pomodoro_focus: z.coerce.number().min(1).max(120),
  pomodoro_break: z.coerce.number().min(1).max(60),
  assignment_reminders: z.boolean(),
  daily_briefing: z.boolean(),
  email_monitoring: z.boolean(),
  notification_enabled: z.boolean(),
});

type SettingsForm = z.infer<typeof settingsSchema>;

export function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      theme: "dark",
      daily_goal_hours: 2,
      pomodoro_focus: 25,
      pomodoro_break: 5,
      assignment_reminders: true,
      daily_briefing: true,
      email_monitoring: false,
      notification_enabled: true,
    },
  });

  useEffect(() => {
    async function load() {
      try {
        const settings = await getMySettings();
        form.reset({
          theme: settings.theme as "dark" | "light" | "system",
          daily_goal_hours: settings.daily_goal_hours,
          pomodoro_focus: settings.pomodoro_focus,
          pomodoro_break: settings.pomodoro_break,
          assignment_reminders: settings.assignment_reminders,
          daily_briefing: settings.daily_briefing,
          email_monitoring: settings.email_monitoring,
          notification_enabled: settings.notification_enabled,
        });
      } catch (err) {
        logger.error("Failed to load settings", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [form]);

  const onSubmit = form.handleSubmit(async (data) => {
    setSaving(true);
    setSaved(false);
    try {
      await updateMySettings(data);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      logger.error("Failed to save settings", err);
    } finally {
      setSaving(false);
    }
  });

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Customize your Fixly experience</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-8">
        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Theme</h2>
          <div className="flex gap-3">
            {(["dark", "light", "system"] as const).map((t) => (
              <label
                key={t}
                className="flex cursor-pointer items-center gap-2 rounded-lg border p-3 has-[:checked]:border-primary has-[:checked]:bg-primary/5"
              >
                <input type="radio" value={t} {...form.register("theme")} className="accent-primary" />
                <span className="text-sm capitalize">{t}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Productivity</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="daily_goal_hours">Daily Goal (hours)</Label>
              <Input id="daily_goal_hours" type="number" min={0} max={24} {...form.register("daily_goal_hours")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pomodoro_focus">Focus Duration (min)</Label>
              <Input id="pomodoro_focus" type="number" min={1} max={120} {...form.register("pomodoro_focus")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pomodoro_break">Break Duration (min)</Label>
              <Input id="pomodoro_break" type="number" min={1} max={60} {...form.register("pomodoro_break")} />
            </div>
          </div>
        </section>

        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Notifications</h2>
          <div className="space-y-3">
            {[
              { key: "notification_enabled" as const, label: "Enable notifications" },
              { key: "assignment_reminders" as const, label: "Assignment reminders" },
              { key: "daily_briefing" as const, label: "Daily briefing" },
              { key: "email_monitoring" as const, label: "Email monitoring" },
            ].map(({ key, label }) => (
              <label key={key} className="flex cursor-pointer items-center gap-3">
                <input type="checkbox" {...form.register(key)} className="h-4 w-4 accent-primary" />
                <span className="text-sm">{label}</span>
              </label>
            ))}
          </div>
        </section>

        <div className="flex items-center gap-4">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
          {saved && (
            <motion.span
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-sm text-success"
            >
              Settings saved
            </motion.span>
          )}
        </div>
      </form>
    </div>
  );
}
