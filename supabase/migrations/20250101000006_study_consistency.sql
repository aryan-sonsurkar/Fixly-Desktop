-- Migration: 20250101000006
-- Description: Study Consistency System tables

CREATE TABLE IF NOT EXISTS study_days (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  total_study_minutes INTEGER DEFAULT 0,
  pomodoro_sessions INTEGER DEFAULT 0,
  assignments_completed INTEGER DEFAULT 0,
  subjects_studied TEXT[] DEFAULT '{}',
  ai_conversations INTEGER DEFAULT 0,
  study_points INTEGER DEFAULT 0,
  mood TEXT CHECK (mood IN ('great', 'good', 'okay', 'bad', 'terrible', NULL)),
  productivity_rating INTEGER CHECK (productivity_rating >= 1 AND productivity_rating <= 10),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date)
);

CREATE TABLE IF NOT EXISTS study_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  activity_type TEXT NOT NULL CHECK (activity_type IN (
    'pomodoro', 'assignment', 'ai_study', 'reading', 'manual', 'email', 'ocr', 'pdf_analysis', 'quiz', 'flashcard', 'revision'
  )),
  points INTEGER NOT NULL DEFAULT 0,
  duration_minutes INTEGER DEFAULT 0,
  subject_id UUID,
  metadata JSONB DEFAULT '{}',
  session_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migrate old study_sessions schema if it exists (created by initial_schema)
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'study_sessions' AND table_schema = 'public') THEN
    ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS activity_type TEXT;
    ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS points INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
    ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS session_date DATE NOT NULL DEFAULT CURRENT_DATE;
    ALTER TABLE study_sessions ALTER COLUMN user_id SET NOT NULL;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS study_points_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_type TEXT NOT NULL UNIQUE,
  points INTEGER NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO study_points_config (activity_type, points, description) VALUES
  ('pomodoro', 10, 'Completed Pomodoro session'),
  ('assignment', 25, 'Assignment completed'),
  ('ai_study', 8, 'AI-assisted study session'),
  ('reading', 5, 'Reading notes'),
  ('manual', 6, 'Manual study log'),
  ('email', 3, 'Email intelligence processed'),
  ('ocr', 4, 'OCR document processed'),
  ('pdf_analysis', 7, 'PDF analysis completed'),
  ('quiz', 12, 'Quiz solved'),
  ('flashcard', 4, 'Flashcard reviewed'),
  ('revision', 15, 'Revision session completed')
ON CONFLICT (activity_type) DO NOTHING;

CREATE TABLE IF NOT EXISTS study_notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date)
);

ALTER TABLE study_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_points_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY study_days_user_policy ON study_days
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY study_sessions_user_policy ON study_sessions
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY study_points_config_read_policy ON study_points_config
  FOR SELECT USING (TRUE);

CREATE POLICY study_notes_user_policy ON study_notes
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_study_days_user_date ON study_days(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_date ON study_sessions(user_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_study_sessions_activity ON study_sessions(user_id, activity_type);
CREATE INDEX IF NOT EXISTS idx_study_notes_user_date ON study_notes(user_id, date DESC);
