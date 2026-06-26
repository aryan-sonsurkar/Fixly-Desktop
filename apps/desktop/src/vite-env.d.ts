/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_FEATURE_GEMINI: string;
  readonly VITE_FEATURE_EMAIL_INTELLIGENCE: string;
  readonly VITE_FEATURE_OCR: string;
  readonly VITE_FEATURE_EXPERIMENTAL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
