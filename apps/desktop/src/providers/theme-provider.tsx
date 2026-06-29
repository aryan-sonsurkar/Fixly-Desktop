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
    root.classList.remove("light", "dark", "dark-cyberpunk");
    root.classList.add(theme);
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
  }, [theme]);

  return <>{children}</>;
}
