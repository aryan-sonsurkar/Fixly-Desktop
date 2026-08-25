-- Migration: 20250101000013
-- Description: Persist the user's selected Ollama model in existing settings

ALTER TABLE settings ADD COLUMN IF NOT EXISTS provider_model TEXT;