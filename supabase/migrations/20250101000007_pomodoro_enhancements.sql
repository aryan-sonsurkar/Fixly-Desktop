-- Migration: 20250101000007
-- Description: Pomodoro timer enhancements - settings, new session fields

CREATE TABLE IF NOT EXISTS pomodoro_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  focus_duration INTEGER NOT NULL DEFAULT 25,
  short_break_duration INTEGER NOT NULL DEFAULT 5,
  long_break_duration INTEGER NOT NULL DEFAULT 15,
  long_break_interval INTEGER NOT NULL DEFAULT 4,
  daily_goal INTEGER NOT NULL DEFAULT 8,
  auto_start_breaks BOOLEAN NOT NULL DEFAULT false,
  auto_start_focus BOOLEAN NOT NULL DEFAULT false,
  sound_enabled BOOLEAN NOT NULL DEFAULT true,
  ticking_sound BOOLEAN NOT NULL DEFAULT false,
  desktop_notifications BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

ALTER TABLE pomodoro_sessions
  ADD COLUMN IF NOT EXISTS interruptions INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS notes TEXT,
  ADD COLUMN IF NOT EXISTS mood_after TEXT CHECK (mood_after IN ('great', 'good', 'okay', 'bad', 'terrible', NULL)),
  ADD COLUMN IF NOT EXISTS subject_id UUID,
  ADD COLUMN IF NOT EXISTS daily_goal_progress REAL DEFAULT 0;

ALTER TABLE pomodoro_sessions
  ALTER COLUMN focus_duration SET DEFAULT 25,
  ALTER COLUMN break_duration SET DEFAULT 5;

ALTER TABLE pomodoro_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY pomodoro_settings_user_policy ON pomodoro_settings
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_pomodoro_settings_user ON pomodoro_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_pomodoro_sessions_subject ON pomodoro_sessions(user_id, subject_id);

CREATE TRIGGER set_pomodoro_settings_updated_at
  BEFORE UPDATE ON pomodoro_settings
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();
