import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button, Input, Label, Skeleton } from "@fixly/ui";
import { getMyProfile, updateMyProfile } from "@/lib/profile-service";
import { createLogger } from "@/lib/logger";

const logger = createLogger("profile-page");

const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  display_name: z.string().optional(),
  education_type: z.string().optional(),
  education_year: z.string().optional(),
  college_name: z.string().optional(),
  university_board: z.string().optional(),
  branch_stream: z.string().optional(),
  division: z.string().optional(),
  roll_number: z.string().optional(),
});

type ProfileForm = z.infer<typeof profileSchema>;

export function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const form = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      display_name: "",
      education_type: "",
      education_year: "",
      college_name: "",
      university_board: "",
      branch_stream: "",
      division: "",
      roll_number: "",
    },
  });

  useEffect(() => {
    async function load() {
      try {
        const profile = await getMyProfile();
        form.reset({
          full_name: profile.full_name || "",
          display_name: profile.display_name || "",
          education_type: profile.education_type || "",
          education_year: profile.education_year || "",
          college_name: profile.college_name || "",
          university_board: profile.university_board || "",
          branch_stream: profile.branch_stream || "",
          division: profile.division || "",
          roll_number: profile.roll_number || "",
        });
      } catch (err) {
        logger.error("Failed to load profile", err);
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
      await updateMyProfile(data);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      logger.error("Failed to save profile", err);
    } finally {
      setSaving(false);
    }
  });

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl space-y-8 p-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-4 w-56" />
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-6 w-24" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-sm text-muted-foreground">Manage your academic identity</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-8">
        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Personal</h2>
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input id="full_name" {...form.register("full_name")} />
            {form.formState.errors.full_name && (
              <p className="text-xs text-destructive">{form.formState.errors.full_name.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="display_name">Display Name <span className="text-muted-foreground">(optional)</span></Label>
            <Input id="display_name" {...form.register("display_name")} />
          </div>
        </section>

        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Academic</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="education_type">Education Type</Label>
              <Input id="education_type" {...form.register("education_type")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="education_year">Year</Label>
              <Input id="education_year" {...form.register("education_year")} />
            </div>
          </div>
        </section>

        <section className="space-y-4 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">Institution</h2>
          <div className="space-y-2">
            <Label htmlFor="college_name">College Name</Label>
            <Input id="college_name" {...form.register("college_name")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="university_board">University / Board</Label>
            <Input id="university_board" {...form.register("university_board")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="branch_stream">Branch / Stream</Label>
            <Input id="branch_stream" {...form.register("branch_stream")} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="division">Division</Label>
              <Input id="division" {...form.register("division")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="roll_number">Roll Number</Label>
              <Input id="roll_number" {...form.register("roll_number")} />
            </div>
          </div>
        </section>

        <div className="flex items-center gap-4">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Profile"}
          </Button>
          {saved && (
            <motion.span
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-sm text-success"
            >
              Profile saved
            </motion.span>
          )}
        </div>
      </form>
    </div>
  );
}
