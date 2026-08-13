-- Migration: 20250101000011
-- Description: Enable RLS on conversations and messages with strict user ownership.
-- Messages are owned by their author AND must belong to a conversation the user owns,
-- preventing cross-user read/insert/update/delete.

-- ============================================
-- CONVERSATIONS
-- ============================================
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_view_policy ON conversations
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY conversations_insert_policy ON conversations
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY conversations_update_policy ON conversations
  FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY conversations_delete_policy ON conversations
  FOR DELETE USING (user_id = auth.uid());

-- ============================================
-- MESSAGES
-- ============================================
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY messages_view_policy ON messages
  FOR SELECT USING (
    user_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  );

CREATE POLICY messages_insert_policy ON messages
  FOR INSERT WITH CHECK (
    user_id = auth.uid()
    AND EXISTS (
      SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  );

CREATE POLICY messages_update_policy ON messages
  FOR UPDATE USING (
    user_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  ) WITH CHECK (
    user_id = auth.uid()
    AND EXISTS (
      SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  );

CREATE POLICY messages_delete_policy ON messages
  FOR DELETE USING (
    user_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid()
    )
  );
