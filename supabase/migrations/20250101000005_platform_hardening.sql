-- Migration: 20250101000005
-- Description: Add missing columns for AI platform features

-- messages table: add feedback column
ALTER TABLE messages ADD COLUMN IF NOT EXISTS feedback TEXT CHECK (feedback IN ('like', 'dislike', NULL));

-- conversations table: add is_pinned and is_archived columns
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- settings table: add AI-related columns
ALTER TABLE settings ADD COLUMN IF NOT EXISTS preferred_provider TEXT DEFAULT 'auto';
ALTER TABLE settings ADD COLUMN IF NOT EXISTS temperature REAL DEFAULT 0.7;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 2048;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS system_prompt TEXT;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS streaming_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS fallback_provider TEXT DEFAULT 'auto';
ALTER TABLE settings ADD COLUMN IF NOT EXISTS ai_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS academic_context BOOLEAN DEFAULT TRUE;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS conversation_memory INTEGER DEFAULT 50;

-- Indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_pinned ON conversations(user_id, is_pinned DESC, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_user_archived ON conversations(user_id, is_archived, updated_at DESC);
