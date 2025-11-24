"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  // load initial theme
  useEffect(() => {
    setMounted(true);
    const stored = window.localStorage.getItem("leadflux-theme") as Theme | null;

    if (stored === "light" || stored === "dark") {
      applyTheme(stored);
      return;
    }

    // fallback to system preference
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark ? "dark" : "light");
  }, []);

  const applyTheme = (t: Theme) => {
    setThemeState(t);
    const root = document.documentElement;
    if (t === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    window.localStorage.setItem("leadflux-theme", t);
  };

  const value: ThemeContextValue = {
    theme,
    toggleTheme: () => applyTheme(theme === "dark" ? "light" : "dark"),
    setTheme: applyTheme,
  };

  // Always provide the context, even before mounted
  // This prevents "useTheme must be used within ThemeProvider" errors
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}

