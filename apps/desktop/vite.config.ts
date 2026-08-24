import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
  build: {
    sourcemap: false,
    minify: "esbuild",
    cssMinify: true,
    reportCompressedSize: true,
    chunkSizeWarningLimit: 300,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          motion: ["framer-motion"],
          query: ["@tanstack/react-query"],
          forms: ["react-hook-form", "@hookform/resolvers", "zod"],
          ui: ["@fixly/ui", "@fixly/shared-types", "@fixly/shared-utils"],
        },
      },
      treeshake: true,
    },
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react-router-dom", "@tanstack/react-query", "axios", "zustand"],
    exclude: ["@tauri-apps/api", "@tauri-apps/plugin-http", "@tauri-apps/plugin-store"],
  },
  esbuild: {
    drop: process.env.NODE_ENV === "production" ? ["console", "debugger"] : [],
    legalComments: "none",
  },
});
