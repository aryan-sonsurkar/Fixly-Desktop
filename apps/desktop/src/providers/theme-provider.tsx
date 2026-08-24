import { useEffect, type ReactNode } from "react";
import { useUIStore } from "@/stores/ui-store";
import { STORAGE_KEYS } from "@fixly/shared-utils";

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme, setTheme } = useUIStore();

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.THEME);
    if (stored === "light" || stored === "dark" || stored === "dark-cyberpunk") {
      setTheme(stored);
    }
  }, [setTheme]);

  useEffect(() => {
    const root = document.documentElement;
    const resolved = theme === "system" ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : theme;
    root.classList.remove("light", "dark", "dark-cyberpunk");
    root.classList.add(resolved);
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
    if (theme === "system") {
      const m = window.matchMedia("(prefers-color-scheme: dark)");
      const onChange = (e: MediaQueryListEvent) => {
        root.classList.remove("light", "dark", "dark-cyberpunk");
        root.classList.add(e.matches ? "dark" : "light");
      };
      m.addEventListener("change", onChange);
      return () => m.removeEventListener("change", onChange);
    }
  }, [theme]);

  return <>{children}</>;
}
