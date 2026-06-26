export const features = {
  ollama: import.meta.env.VITE_FEATURE_OLLAMA !== "false",
  gemini: import.meta.env.VITE_FEATURE_GEMINI === "true",
  emailIntelligence: import.meta.env.VITE_FEATURE_EMAIL_INTELLIGENCE === "true",
  ocr: import.meta.env.VITE_FEATURE_OCR === "true",
  autoUpdater: import.meta.env.VITE_FEATURE_AUTO_UPDATER !== "false",
  experimental: import.meta.env.VITE_FEATURE_EXPERIMENTAL === "true",
} as const;

export type FeatureFlag = keyof typeof features;
