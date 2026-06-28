-- Migration: 20250101000008
-- Description: AI Document Intelligence - documents, chunks, OCR results, document conversations

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  original_name TEXT NOT NULL,
  file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'png', 'jpg', 'jpeg', 'webp')),
  file_size BIGINT NOT NULL,
  page_count INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'processed', 'failed', 'uploading')),
  error_message TEXT,
  processing_time_ms INTEGER,
  storage_path TEXT,
  subject_id UUID,
  is_favorite BOOLEAN DEFAULT FALSE,
  last_opened_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chunk_type TEXT NOT NULL DEFAULT 'text' CHECK (chunk_type IN ('text', 'heading', 'table', 'code', 'list', 'image')),
  content TEXT NOT NULL,
  heading TEXT,
  page_number INTEGER,
  token_count INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_ocr_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  extracted_text TEXT NOT NULL,
  confidence REAL DEFAULT 0,
  processing_time_ms INTEGER DEFAULT 0,
  engine TEXT NOT NULL DEFAULT 'builtin',
  raw_data JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(document_id)
);

CREATE TABLE IF NOT EXISTS document_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(document_id, conversation_id)
);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_ocr_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY documents_user_policy ON documents
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY document_chunks_user_policy ON document_chunks
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY document_ocr_results_user_policy ON document_ocr_results
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY document_conversations_user_policy ON document_conversations
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(user_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user ON document_chunks(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_document_conversations_doc ON document_conversations(document_id);
CREATE INDEX IF NOT EXISTS idx_document_conversations_conv ON document_conversations(conversation_id);

CREATE TRIGGER set_documents_updated_at
  BEFORE UPDATE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();
