import { AnimatePresence, motion } from "motion/react";
import { FileText, Lock, Moon, Sun } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { FlowRail } from "./FlowRail";
import { SilkBackground } from "./SilkBackground";

type Theme = "dark" | "light";

function useTheme(): [Theme, () => void] {
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

function ThemeToggle({ theme, toggle }: { theme: Theme; toggle: () => void }) {
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

export function AppShell({ children }: { children: ReactNode }) {
  const [theme, toggleTheme] = useTheme();

  return (
    <div className="flex min-h-full flex-col font-sans">
      <SilkBackground theme={theme} />
      <header className="sticky top-0 z-40 border-b border-border bg-background/70 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-foreground">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-primary to-violet-500 text-white shadow-glow">
              <FileText className="h-4 w-4" />
            </span>
            ManuScript AI
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex">
              <Lock className="h-3.5 w-3.5" aria-hidden="true" />
              Processed locally — your manuscript never leaves this machine
            </span>
            <ThemeToggle theme={theme} toggle={toggleTheme} />
          </div>
        </div>
      </header>
      <main className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <FlowRail />
        {children}
      </main>
      <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
        ManuScript AI · rule-based, offline-capable · IEEE and Springer format profiles
      </footer>
    </div>
  );
}
