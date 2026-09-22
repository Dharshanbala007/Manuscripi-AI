// Extracted out of AppShell so GlassNavBar can render the same toggle inside its pill.
import { AnimatePresence, motion } from "motion/react";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof document === "undefined") return "dark";
    return (document.documentElement.dataset.theme as Theme | undefined) ?? "dark";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* private browsing / storage disabled — theme just won't persist */
    }
  }, [theme]);

  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

export function ThemeToggle({ theme, toggle }: { theme: Theme; toggle: () => void }) {
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={isDark}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      className="relative grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-full border border-border text-muted-foreground transition-colors hover:text-foreground"
    >
      <AnimatePresence initial={false} mode="popLayout">
        <motion.span
          key={theme}
          initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
          transition={{ type: "spring", stiffness: 400, damping: 26 }}
          className="grid place-items-center"
        >
          {isDark ? <Moon className="h-3.5 w-3.5" aria-hidden="true" /> : <Sun className="h-3.5 w-3.5" aria-hidden="true" />}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
