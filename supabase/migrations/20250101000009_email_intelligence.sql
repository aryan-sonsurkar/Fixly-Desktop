-- Migration: 20250101000009
-- Description: Email Intelligence - messages, classifications, assignment detection, attachments

ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS sync_status TEXT DEFAULT 'idle' CHECK (sync_status IN ('idle', 'syncing', 'error', 'paused'));
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS sync_error TEXT;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS total_emails INTEGER DEFAULT 0;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS last_message_id TEXT;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS daily_briefing_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS briefing_time TEXT DEFAULT '08:00';
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS auto_create_assignments BOOLEAN DEFAULT FALSE;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS confidence_threshold REAL DEFAULT 0.70;
ALTER TABLE email_accounts ADD COLUMN IF NOT EXISTS attachment_download BOOLEAN DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS email_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES email_accounts(id) ON DELETE CASCADE,
  message_id TEXT NOT NULL,
  thread_id TEXT,
  subject TEXT NOT NULL DEFAULT '',
  from_name TEXT,
  from_email TEXT NOT NULL,
  to_emails TEXT[] DEFAULT '{}',
  cc_emails TEXT[] DEFAULT '{}',
  body_text TEXT,
  body_html TEXT,
  received_at TIMESTAMPTZ NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  is_starred BOOLEAN DEFAULT FALSE,
  has_attachments BOOLEAN DEFAULT FALSE,
  labels TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, message_id)
);

CREATE TABLE IF NOT EXISTS email_classifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN (
    'assignment', 'exam', 'project', 'notice', 'holiday', 'event', 'general', 'spam'
  )),
  confidence REAL NOT NULL DEFAULT 0,
  is_reviewed BOOLEAN DEFAULT FALSE,
  user_feedback TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email_id)
);

CREATE TABLE IF NOT EXISTS email_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subject TEXT,
  title TEXT,
  due_date TIMESTAMPTZ,
  priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
  teacher_name TEXT,
  description TEXT,
  course TEXT,
  confidence REAL NOT NULL DEFAULT 0,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'edited', 'rejected', 'converted')),
  assignment_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email_id)
);

CREATE TABLE IF NOT EXISTS email_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID NOT NULL REFERENCES email_messages(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  file_type TEXT,
  file_size INTEGER DEFAULT 0,
  storage_path TEXT,
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE email_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY email_messages_user_policy ON email_messages
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY email_classifications_user_policy ON email_classifications
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY email_assignments_user_policy ON email_assignments
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY email_attachments_user_policy ON email_attachments
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_email_messages_user ON email_messages(user_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_messages_account ON email_messages(account_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_messages_unread ON email_messages(user_id) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_email_classifications_email ON email_classifications(email_id);
CREATE INDEX IF NOT EXISTS idx_email_classifications_category ON email_classifications(user_id, category);
CREATE INDEX IF NOT EXISTS idx_email_assignments_status ON email_assignments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_email_assignments_email ON email_assignments(email_id);
CREATE INDEX IF NOT EXISTS idx_email_attachments_email ON email_attachments(email_id);
CREATE INDEX IF NOT EXISTS idx_email_attachments_unprocessed ON email_attachments(user_id) WHERE processed = FALSE;
