import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button, Input, Label } from "@fixly/ui";
import type { PomodoroSettingsData } from "@/lib/pomodoro-service";

interface PomodoroSettingsProps {
  open: boolean;
  settings: PomodoroSettingsData | null;
  onSave: (settings: Partial<PomodoroSettingsData>) => void;
  onClose: () => void;
}

export function PomodoroSettings({ open, settings, onSave, onClose }: PomodoroSettingsProps) {
  const [form, setForm] = useState({
    focus_duration: 25,
    short_break_duration: 5,
    long_break_duration: 15,
    long_break_interval: 4,
    daily_goal: 8,
    auto_start_breaks: false,
    auto_start_focus: false,
    sound_enabled: true,
    ticking_sound: false,
    desktop_notifications: true,
  });

  useEffect(() => {
    if (settings) {
      setForm({
        focus_duration: settings.focus_duration,
        short_break_duration: settings.short_break_duration,
        long_break_duration: settings.long_break_duration,
        long_break_interval: settings.long_break_interval,
        daily_goal: settings.daily_goal,
        auto_start_breaks: settings.auto_start_breaks,
        auto_start_focus: settings.auto_start_focus,
        sound_enabled: settings.sound_enabled,
        ticking_sound: settings.ticking_sound,
        desktop_notifications: settings.desktop_notifications,
      });
    }
  }, [settings]);

  const handleSubmit = () => {
    onSave(form);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Timer Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <Label>Focus (min)</Label>
              <Input
                type="number" min={1} max={120}
                value={form.focus_duration}
                onChange={(e) => setForm({ ...form, focus_duration: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Short Break</Label>
              <Input
                type="number" min={1} max={30}
                value={form.short_break_duration}
                onChange={(e) => setForm({ ...form, short_break_duration: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Long Break</Label>
              <Input
                type="number" min={1} max={60}
                value={form.long_break_duration}
                onChange={(e) => setForm({ ...form, long_break_duration: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Long Break Interval</Label>
              <Input
                type="number" min={1} max={10}
                value={form.long_break_interval}
                onChange={(e) => setForm({ ...form, long_break_interval: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Daily Goal (cycles)</Label>
              <Input
                type="number" min={1} max={50}
                value={form.daily_goal}
                onChange={(e) => setForm({ ...form, daily_goal: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium">Preferences</Label>
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.auto_start_breaks}
                  onChange={(e) => setForm({ ...form, auto_start_breaks: e.target.checked })} />
                Auto-start breaks
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.auto_start_focus}
                  onChange={(e) => setForm({ ...form, auto_start_focus: e.target.checked })} />
                Auto-start focus
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.sound_enabled}
                  onChange={(e) => setForm({ ...form, sound_enabled: e.target.checked })} />
                Sound
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.ticking_sound}
                  onChange={(e) => setForm({ ...form, ticking_sound: e.target.checked })} />
                Ticking
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.desktop_notifications}
                  onChange={(e) => setForm({ ...form, desktop_notifications: e.target.checked })} />
                Notifications
              </label>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Save</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
